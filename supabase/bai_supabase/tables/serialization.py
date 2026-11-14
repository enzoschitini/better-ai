"""(De)serialização dict <-> entidade (research/06 §6 e §8).

O formato "wire" é o JSON que trafega no PostgREST. A entidade é definida por
``TableDescriptor.model``: ``None`` (``dict``), uma ``dataclass`` ou uma classe com
``model_validate``/``model_dump`` (estilo Pydantic, sem exigir Pydantic).

Regras: datetime exige fuso (ingênuo é recusado); colunas gerenciadas pelo servidor não
são enviadas; erros citam TABELA e CAMPO, nunca o valor.
"""

from __future__ import annotations

import dataclasses
import enum
import math
import types
import typing
from collections.abc import Collection, Mapping
from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Any, Optional, Union
from uuid import UUID

from bai_supabase.contracts.tables import TableDescriptor
from bai_supabase.errors.exceptions import ConfigurationError, MappingError, ValidationError

DICT = "dict"
DATACLASS = "dataclass"
PYDANTIC = "pydantic"


def entity_kind(model: Optional[type]) -> str:
    """Classifica o ``model`` do descritor; ``ConfigurationError`` se não for suportado."""
    if model is None:
        return DICT
    if isinstance(model, type) and dataclasses.is_dataclass(model):
        return DATACLASS
    if hasattr(model, "model_validate") and hasattr(model, "model_dump"):
        return PYDANTIC
    raise ConfigurationError("modelo do descritor não suportado: use None, dataclass ou classe com model_validate/model_dump")


def to_wire_value(value: Any, *, table: str, field: str) -> Any:
    """Converte um valor Python para um valor JSON-compatível (nunca ``default=str`` genérico)."""
    if isinstance(value, enum.Enum):
        return to_wire_value(value.value, table=table, field=field)
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValidationError(f"número não finito no campo '{field}' da tabela '{table}'", resource=table)
        return value
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValidationError(f"decimal não finito no campo '{field}' da tabela '{table}'", resource=table)
        return str(value)  # string preserva a precisão (nada de float)
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValidationError(
                f"datetime sem fuso horário no campo '{field}' da tabela '{table}'", resource=table
            )
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, (date, time)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Mapping):
        out = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise MappingError(f"chave não textual em json no campo '{field}' da tabela '{table}'", resource=table)
            out[key] = to_wire_value(item, table=table, field=field)
        return out
    if isinstance(value, (list, tuple)):
        return [to_wire_value(item, table=table, field=field) for item in value]
    if isinstance(value, (set, frozenset)):
        converted = [to_wire_value(item, table=table, field=field) for item in value]
        return sorted(converted, key=repr)  # ordem determinística
    raise MappingError(
        f"tipo não suportado ({type(value).__name__}) no campo '{field}' da tabela '{table}'", resource=table
    )


class EntityCodec:
    """Codec de uma tabela: ``entidade|dict`` <-> ``dict`` JSON-compatível."""

    def __init__(self, descriptor: TableDescriptor) -> None:
        self._descriptor = descriptor
        self._table = descriptor.name
        self._model = descriptor.model
        self.kind = entity_kind(descriptor.model)

    # ------------------------------------------------------------------ escrita
    def to_mapping(self, entity: Any) -> dict:
        """Extrai um ``dict`` (valores Python) da entidade; ``dict`` é aceito sempre."""
        if isinstance(entity, Mapping):
            return dict(entity)
        if self._model is not None and isinstance(entity, self._model):
            if self.kind == DATACLASS:
                return {f.name: getattr(entity, f.name) for f in dataclasses.fields(entity)}
            return dict(entity.model_dump(by_alias=True))
        raise ValidationError(f"entidade de tipo incompatível para a tabela '{self._table}'", resource=self._table)

    def to_changes_mapping(self, changes: Any) -> dict:
        """Mapeia ``changes`` (dict, ou modelo Pydantic com ``exclude_unset``)."""
        if isinstance(changes, Mapping):
            return dict(changes)
        if self.kind == PYDANTIC and isinstance(changes, self._model):
            return dict(changes.model_dump(by_alias=True, exclude_unset=True))
        raise ValidationError(f"alterações devem ser um dict (tabela '{self._table}')", resource=self._table)

    def encode_insert(self, mapping: Mapping, *, allowed_managed: Collection[str] = ()) -> dict:
        """Linha para insert/upsert: remove colunas do servidor vazias; recusa as preenchidas.

        ``allowed_managed``: colunas gerenciadas que podem ser enviadas (ex.: PK no upsert).
        """
        managed = set(self._descriptor.server_managed_columns)
        row: dict = {}
        for column, value in mapping.items():
            if column in managed and column not in allowed_managed:
                if value is None:
                    continue
                raise ValidationError(
                    f"escrita na coluna gerenciada pelo servidor '{column}' da tabela '{self._table}'",
                    resource=self._table,
                )
            row[column] = to_wire_value(value, table=self._table, field=column)
        return row

    def encode_changes(self, mapping: Mapping) -> dict:
        """Linha para update parcial: recusa colunas gerenciadas e a PK."""
        managed = set(self._descriptor.server_managed_columns) | {self._descriptor.primary_key}
        row: dict = {}
        for column, value in mapping.items():
            if column in managed:
                raise ValidationError(
                    f"alteração da coluna '{column}' (gerenciada/PK) da tabela '{self._table}' não é permitida",
                    resource=self._table,
                )
            row[column] = to_wire_value(value, table=self._table, field=column)
        return row

    def wire(self, value: Any, field: str) -> Any:
        """Converte um valor isolado (filtros, ids) para o formato JSON."""
        return to_wire_value(value, table=self._table, field=field)

    # ------------------------------------------------------------------ leitura
    def decode(self, row: Any) -> Any:
        """Converte uma linha JSON na entidade do descritor (colunas extras são toleradas)."""
        if not isinstance(row, Mapping):
            raise MappingError(f"linha inválida recebida da tabela '{self._table}'", resource=self._table)
        if self.kind == DICT:
            return dict(row)
        if self.kind == PYDANTIC:
            return self._decode_pydantic(row)
        return self._decode_dataclass(row)

    def _decode_pydantic(self, row: Mapping) -> Any:
        try:
            return self._model.model_validate(dict(row))
        except Exception as exc:  # noqa: BLE001 - qualquer falha do modelo vira MappingError
            fields = _failed_fields(exc)
            detail = f" (campos: {', '.join(fields)})" if fields else ""
            raise MappingError(
                f"falha ao mapear registro da tabela '{self._table}'{detail}", resource=self._table
            ) from exc

    def _decode_dataclass(self, row: Mapping) -> Any:
        try:
            hints = typing.get_type_hints(self._model)
        except Exception:  # noqa: BLE001 - anotações não resolvíveis: sem coerção
            hints = {}
        kwargs: dict = {}
        for fld in dataclasses.fields(self._model):
            if not fld.init:
                continue
            if fld.name in row:
                kwargs[fld.name] = self._coerce(row[fld.name], hints.get(fld.name, Any), fld.name)
            elif fld.default is dataclasses.MISSING and fld.default_factory is dataclasses.MISSING:
                raise MappingError(
                    f"campo '{fld.name}' ausente na linha da tabela '{self._table}'", resource=self._table
                )
        return self._model(**kwargs)

    def _coerce(self, value: Any, hint: Any, field: str) -> Any:
        if value is None or hint is Any:
            return value
        origin = typing.get_origin(hint)
        args = typing.get_args(hint)
        if origin is Union or origin is types.UnionType:
            return self._coerce_union(value, args, field)
        if origin in (list, set, frozenset, tuple) and isinstance(value, list):
            inner = args[0] if args else Any
            items = [self._coerce(v, inner, field) for v in value]
            return origin(items) if origin is not list else items
        try:
            return _convert_scalar(value, hint)
        except (ValueError, TypeError, ArithmeticError) as exc:
            raise MappingError(
                f"campo '{field}' da tabela '{self._table}' incompatível com o tipo declarado", resource=self._table
            ) from exc

    def _coerce_union(self, value: Any, args: tuple, field: str) -> Any:
        last: Optional[MappingError] = None
        for arg in args:
            if arg is type(None):
                continue
            try:
                return self._coerce(value, arg, field)
            except MappingError as exc:
                last = exc
        assert last is not None
        raise last


def _convert_scalar(value: Any, hint: Any) -> Any:
    """Converte ``value`` JSON para o tipo ``hint``; tipos desconhecidos passam sem alteração."""
    if not isinstance(hint, type):
        return value
    if hint is bool:
        if not isinstance(value, bool):
            raise TypeError("bool esperado")
        return value
    if hint is int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("int esperado")
        return value
    if hint is float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("float esperado")
        return float(value)
    if hint is str:
        if not isinstance(value, str):
            raise TypeError("str esperado")
        return value
    if hint is Decimal:
        if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
            raise TypeError("decimal esperado")
        return Decimal(str(value))  # via texto: sem erro de ponto flutuante extra
    if hint is UUID:
        return value if isinstance(value, UUID) else UUID(str(value))
    if hint is datetime:
        if isinstance(value, datetime):
            return _to_utc(value)
        return _to_utc(datetime.fromisoformat(value))
    if hint is date:
        return value if isinstance(value, date) and not isinstance(value, datetime) else date.fromisoformat(value)
    if hint is time:
        return value if isinstance(value, time) else time.fromisoformat(value)
    if issubclass(hint, enum.Enum):
        return value if isinstance(value, hint) else hint(value)
    return value


def _to_utc(value: datetime) -> datetime:
    """Datetime com fuso vai para UTC; sem fuso (coluna ``timestamp``) permanece como veio."""
    return value.astimezone(timezone.utc) if value.tzinfo is not None else value


def _failed_fields(exc: Exception) -> list[str]:
    """Nomes dos campos que falharam na validação (sem ``input``: nunca os valores)."""
    try:
        errors = exc.errors()  # type: ignore[attr-defined]
        names = {str(err["loc"][0]) for err in errors if err.get("loc")}
        return sorted(names)
    except Exception:  # noqa: BLE001
        return []
