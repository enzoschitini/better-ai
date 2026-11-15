"""Validação de entrada da frente A (research/05 §6, research/06 §4.4 e §9).

Tudo aqui falha ANTES de ir à rede: nomes (regex + allowlist), operadores, valores de
filtro, colunas de escrita, filtro vazio em update/delete e lote vazio.
Mensagens nunca ecoam valores; nomes são truncados e escapados (``repr``).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any, Iterable, Optional, Sequence

from src.database.supabase_integration.contracts.query import (
    Condition,
    Filter,
    FilterGroup,
    Op,
    Query,
    Sort,
    is_empty_filter,
)
from src.database.supabase_integration.contracts.settings import TablesSettings
from src.database.supabase_integration.contracts.tables import BatchOptions, TableDescriptor
from src.database.supabase_integration.errors.exceptions import ConfigurationError, ValidationError
from src.database.supabase_integration.tables.serialization import entity_kind, to_wire_value

IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")
BATCH_MODES = ("stop", "continue")
MAX_FILTER_DEPTH = 8
MAX_IN_VALUES = 1000
_MAX_ECHO = 40


def safe_name(name: Any) -> str:
    """Versão truncada e escapada de um nome vindo de fora (evita reflexão de entrada)."""
    return repr(str(name)[:_MAX_ECHO])


def validate_identifier(name: Any, kind: str = "identificador") -> str:
    """Valida o formato de um identificador SQL (tabela, schema, coluna)."""
    if not isinstance(name, str) or not IDENTIFIER_RE.fullmatch(name):
        raise ValidationError(f"{kind} inválido: {safe_name(name)}")
    return name


def ensure_table_allowed(name: str, allowlist: Sequence[str]) -> None:
    """``ConfigurationError`` se a tabela não estiver na allowlist (vazia = qualquer uma)."""
    if allowlist and name not in allowlist:
        raise ConfigurationError(f"tabela não permitida: {safe_name(name)}")


def validate_descriptor(descriptor: TableDescriptor, allowlist: Sequence[str] = ()) -> None:
    """Valida um descritor no registro; ``ConfigurationError`` em qualquer inconsistência."""
    try:
        validate_identifier(descriptor.name, "tabela")
        validate_identifier(descriptor.schema, "schema")
        validate_identifier(descriptor.primary_key, "chave primária")
        for col in descriptor.server_managed_columns:
            validate_identifier(col, "coluna gerenciada")
        if descriptor.sort_key is not None:
            validate_identifier(descriptor.sort_key, "chave de ordenação")
        if descriptor.columns is not None:
            if not descriptor.columns:
                raise ValidationError("allowlist de colunas vazia")
            for col in descriptor.columns:
                validate_identifier(col, "coluna")
            for needed in filter(None, (descriptor.primary_key, descriptor.sort_key)):
                if needed not in descriptor.columns:
                    raise ValidationError(f"coluna {safe_name(needed)} deve constar na allowlist de colunas")
    except ValidationError as exc:
        raise ConfigurationError(f"descritor inválido: {exc.message}", resource=descriptor.name) from exc
    ensure_table_allowed(descriptor.name, allowlist)
    entity_kind(descriptor.model)


class TableValidator:
    """Validador por tabela: usa o descritor (colunas) e as configurações (tetos)."""

    def __init__(self, descriptor: TableDescriptor, settings: TablesSettings) -> None:
        self._descriptor = descriptor
        self._settings = settings
        self._table = descriptor.name

    # ------------------------------------------------------------------ nomes
    def column(self, name: Any) -> str:
        """Coluna válida pela regex e pertencente à allowlist do descritor (se houver)."""
        validate_identifier(name, "coluna")
        allowed = self._descriptor.columns
        if allowed is not None and name not in allowed:
            raise ValidationError(f"coluna não permitida: {safe_name(name)}", resource=self._table)
        return name

    def write_columns(self, names: Iterable[Any]) -> None:
        """Colunas de escrita: campos desconhecidos são recusados (mass assignment)."""
        for name in names:
            self.column(name)

    def conflict_columns(self, on_conflict: Optional[str]) -> tuple[str, ...]:
        """Interpreta ``on_conflict`` ("a" ou "a,b"); None = chave primária."""
        if on_conflict is None:
            return (self._descriptor.primary_key,)
        if not isinstance(on_conflict, str) or not on_conflict.strip():
            raise ValidationError("on_conflict inválido", resource=self._table)
        return tuple(self.column(part.strip()) for part in on_conflict.split(","))

    def select_columns(self, requested: Optional[Sequence[str]]) -> Optional[tuple[str, ...]]:
        """Colunas efetivas do select: sem allowlist usa ``*``; com allowlist nunca ``*``."""
        if requested is not None:
            if not requested:
                raise ValidationError("seleção de colunas vazia", resource=self._table)
            return tuple(self.column(c) for c in requested)
        return self._descriptor.columns

    # ------------------------------------------------------------------ consulta
    def query(self, query: Optional[Query]) -> Query:
        """Valida e normaliza a consulta (valores convertidos para o formato JSON)."""
        query = query or Query()
        sorts = tuple(Sort(self.column(s.column), bool(s.descending), s.nulls_first) for s in query.sorts)
        return Query(
            filter=self.filter(query.filter) if query.filter is not None else None,
            sorts=sorts,
            columns=self.select_columns(query.columns),
        )

    def filter(self, node: Filter, _depth: int = 0) -> Filter:
        """Valida a árvore de filtros e converte os valores (datetime exige fuso)."""
        if _depth > MAX_FILTER_DEPTH:
            raise ValidationError("filtro aninhado demais", resource=self._table)
        if isinstance(node, Condition):
            return self._condition(node)
        if isinstance(node, FilterGroup):
            if node.logic not in ("and", "or"):
                raise ValidationError("lógica de grupo inválida (use 'and' ou 'or')", resource=self._table)
            items = tuple(self.filter(i, _depth + 1) for i in node.items)
            return FilterGroup(items=items, logic=node.logic)
        raise ValidationError("filtro inválido", resource=self._table)

    def non_empty_filter(self, node: Optional[Filter], operation: str) -> Filter:
        """Update/delete em massa exigem filtro com ao menos uma condição."""
        if is_empty_filter(node):
            raise ValidationError(f"{operation} recusado: filtro vazio", operation=operation, resource=self._table)
        return self.filter(node)  # type: ignore[arg-type]

    def _condition(self, cond: Condition) -> Condition:
        column = self.column(cond.column)
        try:
            op = cond.op if isinstance(cond.op, Op) else Op(cond.op)
        except ValueError:
            raise ValidationError(f"operador não suportado: {safe_name(cond.op)}", resource=self._table) from None
        return Condition(column, op, self._value(column, op, cond.value))

    def _value(self, column: str, op: Op, value: Any) -> Any:
        wire = lambda v: to_wire_value(v, table=self._table, field=column)  # noqa: E731
        if op in (Op.IS_NULL, Op.NOT_NULL):
            return None
        if op is Op.IN:
            if isinstance(value, (str, bytes, Mapping)) or not isinstance(value, (list, tuple, set, frozenset)):
                raise ValidationError(f"IN exige lista (coluna {safe_name(column)})", resource=self._table)
            if len(value) > MAX_IN_VALUES:
                raise ValidationError(f"IN com valores demais (máx. {MAX_IN_VALUES})", resource=self._table)
            items = [self._scalar(wire(v), column) for v in value]
            return items
        if op in (Op.LIKE, Op.ILIKE):
            if not isinstance(value, str):
                raise ValidationError(f"{op.value} exige texto (coluna {safe_name(column)})", resource=self._table)
            return value
        if op is Op.CONTAINS:
            converted = wire(value)
            if not isinstance(converted, (list, dict, str)):
                raise ValidationError(f"contains exige lista, dict ou texto (coluna {safe_name(column)})", resource=self._table)
            return converted
        return self._scalar(wire(value), column)

    def _scalar(self, value: Any, column: str) -> Any:
        if value is None:
            raise ValidationError(
                f"valor nulo em filtro (coluna {safe_name(column)}); use IS_NULL/NOT_NULL", resource=self._table
            )
        if isinstance(value, (list, dict)):
            raise ValidationError(f"valor escalar esperado (coluna {safe_name(column)})", resource=self._table)
        return value

    # ------------------------------------------------------------------ ids e lotes
    def record_id(self, value: Any) -> Any:
        """Id de registro (str, int ou UUID) convertido para o formato JSON."""
        if value is None or isinstance(value, bool) or isinstance(value, float):
            raise ValidationError("id inválido", resource=self._table)
        wire = to_wire_value(value, table=self._table, field=self._descriptor.primary_key)
        if isinstance(wire, str) and not wire.strip():
            raise ValidationError("id vazio", resource=self._table)
        if not isinstance(wire, (str, int)):
            raise ValidationError("id inválido", resource=self._table)
        return wire

    def non_empty_batch(self, items: Sequence[Any], operation: str) -> list:
        """Lote vazio é erro de validação (A-01)."""
        listed = list(items)
        if not listed:
            raise ValidationError(f"{operation} recusado: lote vazio", operation=operation, resource=self._table)
        return listed

    def batch_options(self, options: Optional[BatchOptions]) -> tuple[int, str]:
        """Resolve ``(batch_size, mode)``; tamanho acima do teto é erro, nunca ajuste silencioso."""
        options = options or BatchOptions()
        size = self._settings.batch_size if options.batch_size is None else options.batch_size
        ceiling = self._settings.server_max_rows
        if isinstance(size, bool) or not isinstance(size, int) or size < 1 or size > ceiling:
            raise ValidationError(f"batch_size deve estar entre 1 e {ceiling}", resource=self._table)
        if options.mode not in BATCH_MODES:
            raise ValidationError("modo de lote inválido (use 'stop' ou 'continue')", resource=self._table)
        return size, options.mode

    def offset(self, value: Any) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValidationError("offset deve ser inteiro >= 0", resource=self._table)
        return value
