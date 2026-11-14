"""Contratos da frente A (tabelas) — research/06, research/09."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator, Optional, Protocol, Sequence, TypeVar, runtime_checkable

from bai_supabase.contracts.query import Filter, Page, PageRequest, Query
from bai_supabase.contracts.results import BatchResult, DeleteResult

E = TypeVar("E")
K = TypeVar("K")


@dataclass(frozen=True)
class TableDescriptor:
    """Descreve uma tabela. Adicionar tabela = novo descritor, sem editar código existente."""

    name: str
    schema: str = "public"
    primary_key: str = "id"
    #: Classe (ex.: Pydantic/dataclass) usada para (de)serializar; None = ``dict``.
    model: Optional[type] = None
    #: Colunas preenchidas pelo servidor (id gerado, created_at...): não enviadas no insert.
    server_managed_columns: tuple[str, ...] = ()
    #: Allowlist de colunas permitidas em filtros/ordenação/escrita (None = sem restrição).
    columns: Optional[tuple[str, ...]] = None
    #: Chave de ordenação estável e NÃO nula para keyset (None = só offset).
    sort_key: Optional[str] = None


@dataclass(frozen=True)
class BatchOptions:
    batch_size: Optional[int] = None  # None = TablesSettings.batch_size
    mode: str = "continue"  # "stop" | "continue"


@runtime_checkable
class TableRepository(Protocol[E, K]):
    """Operações sobre UMA tabela. Todas levantam exceções do domínio."""

    descriptor: TableDescriptor

    def get_by_id(self, id: K) -> E:
        """``RecordNotFoundError`` se não existir."""
        ...

    def find(self, query: Optional[Query] = None) -> list[E]:
        """Lista vazia se não houver linhas; nunca erro por vazio."""
        ...

    def list(self, query: Optional[Query] = None, page: Optional[PageRequest] = None) -> Page[E]: ...

    def iterate(self, query: Optional[Query] = None, page_size: Optional[int] = None) -> Iterator[E]:
        """Varredura preguiçosa sem estourar memória; nunca trunca em silêncio."""
        ...

    def insert(self, entity: E) -> E:
        """Não idempotente: sem retry automático."""
        ...

    def insert_many(self, entities: Sequence[E], options: Optional[BatchOptions] = None) -> BatchResult: ...

    def update(self, id: K, changes: dict) -> E:
        """``RecordNotFoundError`` se não existir."""
        ...

    def update_where(self, filter: Filter, changes: dict) -> int:
        """Recusa filtro vazio (``ValidationError``). Devolve nº de linhas afetadas."""
        ...

    def upsert(self, entity: E, on_conflict: Optional[str] = None) -> E: ...

    def upsert_many(
        self, entities: Sequence[E], on_conflict: Optional[str] = None, options: Optional[BatchOptions] = None
    ) -> BatchResult: ...

    def delete(self, id: K) -> DeleteResult:
        """Idempotente: inexistente = sucesso com ``removed=False``."""
        ...

    def delete_where(self, filter: Filter) -> DeleteResult:
        """Recusa filtro vazio (``ValidationError``)."""
        ...


@runtime_checkable
class TablesContract(Protocol):
    """Classe de tabelas: registro de descritores + acesso a repositórios por tabela."""

    def register(self, descriptor: TableDescriptor) -> None: ...

    def table(self, name: str) -> TableRepository[Any, Any]:
        """``ConfigurationError`` se a tabela não estiver registrada/permitida."""
        ...
