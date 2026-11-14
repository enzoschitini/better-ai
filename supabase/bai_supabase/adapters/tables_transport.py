"""``TableTransport`` sobre o cliente SÍNCRONO do supabase-py (research/06 §4.3).

Este módulo NÃO importa o SDK: recebe um provedor de cliente (callable) por injeção.
Toda chamada ao SDK fica dentro de ``sdk_errors`` (exceção do SDK -> exceção do domínio).
Valores de filtro vão por parâmetros do SDK; só dentro de ``or(...)``/``and(...)`` o
PostgREST exige texto, e ali cada valor é escapado (aspas e barra invertida).
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any, Callable, Optional, Sequence

from bai_supabase.adapters.normalize import sdk_errors
from bai_supabase.contracts.query import Condition, Filter, Op, is_empty_filter
from bai_supabase.contracts.transports import SelectRequest, SelectResponse
from bai_supabase.errors.exceptions import UnexpectedError, ValidationError

_SIMPLE = {
    Op.EQ: "eq", Op.NEQ: "neq", Op.GT: "gt", Op.GTE: "gte", Op.LT: "lt", Op.LTE: "lte",
}
_RESERVED = set(',.:()"\\ \t\n')


def _scalar(value: Any) -> str:
    """Texto de um valor escalar no formato do PostgREST."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (Decimal, int, float, str)):
        return str(value)
    raise ValidationError("valor de filtro não suportado")


def _quote(text: str) -> str:
    """Cita um valor dentro de expressões ``or``/``and``/``in`` quando tem caractere reservado."""
    if text == "" or any(ch in _RESERVED for ch in text):
        return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return text


def _array_literal(items: Sequence[Any]) -> str:
    return "{" + ",".join(_quote(_scalar(i)) for i in items) + "}"


def _contains_literal(value: Any) -> str:
    """Literal para ``cs``: lista -> array do Postgres; dict -> JSON; texto -> como veio."""
    if isinstance(value, dict):
        return json.dumps(value, separators=(",", ":"))
    if isinstance(value, (list, tuple)):
        return _array_literal(value)
    return _scalar(value)


def _leaf_expr(cond: Condition) -> str:
    """``coluna.op.valor`` para uso dentro de ``or(...)``/``and(...)``."""
    col = cond.column
    if cond.op in _SIMPLE:
        return f"{col}.{_SIMPLE[cond.op]}.{_quote(_scalar(cond.value))}"
    if cond.op in (Op.LIKE, Op.ILIKE):
        return f"{col}.{cond.op.value}.{_quote(_scalar(cond.value))}"
    if cond.op is Op.IN:
        return f"{col}.in.({','.join(_quote(_scalar(v)) for v in cond.value)})"
    if cond.op is Op.IS_NULL:
        return f"{col}.is.null"
    if cond.op is Op.NOT_NULL:
        return f"{col}.not.is.null"
    if cond.op is Op.CONTAINS:
        return f"{col}.cs.{_quote(_contains_literal(cond.value))}"
    raise ValidationError("operador não suportado")


def _join(items: Sequence[Filter]) -> str:
    """Itens separados por vírgula (sem o ``or(...)``/``and(...)`` externo); ignora vazios."""
    return ",".join(e for e in (_group_expr(i) for i in items) if e)


def _group_expr(node: Filter) -> str:
    """Expressão de um nó (condição ou grupo); vazio se não houver condição efetiva."""
    if isinstance(node, Condition):
        return _leaf_expr(node)
    parts = [e for e in (_group_expr(i) for i in node.items) if e]
    if len(parts) <= 1:
        return "".join(parts)
    return f"{node.logic}({','.join(parts)})"


class SupabaseTableTransport:
    """Traduz ``SelectRequest``/``Query`` para a cadeia fluente do cliente supabase-py.

    ``client_provider``: callable que devolve o cliente (permite recriá-lo/renová-lo).
    ``default_schema``: schema configurado no cliente; outros usam ``client.schema(s)``.
    """

    def __init__(self, client_provider: Callable[[], Any], *, default_schema: str = "public") -> None:
        self._provider = client_provider
        self._default_schema = default_schema

    def _table(self, schema: str, table: str) -> Any:
        client = self._provider()
        if schema == self._default_schema:
            return client.from_(table)
        return client.schema(schema).from_(table)

    # ------------------------------------------------------------------ filtros
    def _apply(self, builder: Any, node: Optional[Filter]) -> Any:
        """Aplica a árvore: AND encadeia chamadas; grupos OR viram ``or_(...)``."""
        if node is None or is_empty_filter(node):
            return builder
        if isinstance(node, Condition):
            return self._leaf(builder, node)
        items = [i for i in node.items if not is_empty_filter(i)]
        if node.logic == "and" or len(items) == 1:
            for item in items:
                builder = self._apply(builder, item)
            return builder
        return builder.or_(_join(items))  # o SDK já envolve em or(...)

    @staticmethod
    def _leaf(builder: Any, cond: Condition) -> Any:
        col, op, value = cond.column, cond.op, cond.value
        if op is Op.EQ:
            return builder.eq(col, _scalar(value))
        if op is Op.NEQ:
            return builder.neq(col, _scalar(value))
        if op is Op.GT:
            return builder.gt(col, _scalar(value))
        if op is Op.GTE:
            return builder.gte(col, _scalar(value))
        if op is Op.LT:
            return builder.lt(col, _scalar(value))
        if op is Op.LTE:
            return builder.lte(col, _scalar(value))
        if op is Op.LIKE:
            return builder.like(col, _scalar(value))
        if op is Op.ILIKE:
            return builder.ilike(col, _scalar(value))
        if op is Op.IN:
            return builder.filter(col, "in", "(" + ",".join(_quote(_scalar(v)) for v in value) + ")")
        if op is Op.IS_NULL:
            return builder.is_(col, None)
        if op is Op.NOT_NULL:
            return builder.not_.is_(col, None)
        if op is Op.CONTAINS:
            return builder.contains(col, _contains_literal(value))
        raise ValidationError("operador não suportado")

    # ------------------------------------------------------------------ TableTransport
    def select(self, req: SelectRequest) -> SelectResponse:
        with sdk_errors("table", "select", req.table):
            columns = ",".join(req.columns) if req.columns else "*"
            builder = self._table(req.schema, req.table).select(columns, count=req.count)
            builder = self._apply(builder, req.filter)
            for sort in req.sorts:
                builder = builder.order(sort.column, desc=sort.descending, nullsfirst=sort.nulls_first)
            if req.limit is not None:
                builder = builder.range(req.offset, req.offset + req.limit - 1)
            elif req.offset:
                builder = builder.offset(req.offset)
            response = builder.execute()
            return SelectResponse(rows=self._rows(response, "select", req.table), count=response.count)

    def insert(self, table: str, schema: str, rows: Sequence[dict]) -> list[dict]:
        with sdk_errors("table", "insert", table):
            response = self._table(schema, table).insert(list(rows), default_to_null=False).execute()
            return self._rows(response, "insert", table)

    def upsert(self, table: str, schema: str, rows: Sequence[dict], on_conflict: Optional[str] = None,
               ignore_duplicates: bool = False) -> list[dict]:
        with sdk_errors("table", "upsert", table):
            builder = self._table(schema, table).upsert(
                list(rows), on_conflict=on_conflict or "", ignore_duplicates=ignore_duplicates, default_to_null=False
            )
            return self._rows(builder.execute(), "upsert", table)

    def update(self, table: str, schema: str, changes: dict, filter: Filter) -> list[dict]:
        self._require_filter(filter, "update", table)
        with sdk_errors("table", "update", table):
            builder = self._apply(self._table(schema, table).update(dict(changes)), filter)
            return self._rows(builder.execute(), "update", table)

    def delete(self, table: str, schema: str, filter: Filter) -> list[dict]:
        self._require_filter(filter, "delete", table)
        with sdk_errors("table", "delete", table):
            builder = self._apply(self._table(schema, table).delete(), filter)
            return self._rows(builder.execute(), "delete", table)

    # ------------------------------------------------------------------ apoio
    @staticmethod
    def _require_filter(filter: Optional[Filter], operation: str, table: str) -> None:
        """Defesa em profundidade: nunca enviar update/delete sem condição."""
        if is_empty_filter(filter):
            raise ValidationError(f"{operation} sem filtro recusado", operation=f"table.{operation}", resource=table)

    @staticmethod
    def _rows(response: Any, operation: str, table: str) -> list[dict]:
        data = response.data
        if data is None:
            return []
        if not isinstance(data, list):
            raise UnexpectedError("resposta inesperada do PostgREST", operation=f"table.{operation}", resource=table)
        return data
