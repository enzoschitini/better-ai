"""Query Object agnóstico ao SDK (research/06 §4)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Generic, Optional, TypeVar, Union

E = TypeVar("E")


class Op(str, Enum):
    """Operadores v1."""

    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    LIKE = "like"
    ILIKE = "ilike"
    IS_NULL = "is_null"
    NOT_NULL = "not_null"
    CONTAINS = "contains"  # jsonb/array @>


@dataclass(frozen=True)
class Condition:
    column: str
    op: Op
    value: Any = None  # ignorado em IS_NULL/NOT_NULL


@dataclass(frozen=True)
class FilterGroup:
    """Árvore de condições. ``logic`` é "and" ou "or"; itens podem ser grupos."""

    items: tuple[Union[Condition, "FilterGroup"], ...] = ()
    logic: str = "and"


Filter = Union[Condition, FilterGroup]


@dataclass(frozen=True)
class Sort:
    column: str
    descending: bool = False
    nulls_first: Optional[bool] = None


@dataclass(frozen=True)
class Query:
    filter: Optional[Filter] = None
    sorts: tuple[Sort, ...] = ()
    columns: Optional[tuple[str, ...]] = None  # None = todas

    @staticmethod
    def where(*conditions: Condition) -> "Query":
        return Query(filter=FilterGroup(items=tuple(conditions)))

    @staticmethod
    def eq(column: str, value: Any) -> "Query":
        return Query(filter=Condition(column, Op.EQ, value))


def is_empty_filter(f: Optional[Filter]) -> bool:
    """True se não houver nenhuma condição efetiva (usado para recusar update/delete sem filtro)."""
    if f is None:
        return True
    if isinstance(f, Condition):
        return False
    return all(is_empty_filter(i) for i in f.items)


@dataclass(frozen=True)
class PageRequest:
    limit: Optional[int] = None  # None = padrão da configuração
    offset: int = 0
    cursor: Optional[str] = None  # keyset opaco; se presente, ignora offset
    include_count: bool = False


@dataclass(frozen=True)
class Page(Generic[E]):
    items: list
    limit: int
    offset: int = 0
    next_cursor: Optional[str] = None
    total: Optional[int] = None
    has_more: bool = False
