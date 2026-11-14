"""Contratos de transporte: a única fronteira com o SDK (constituição P4).

Implementados em ``adapters/`` (SDK real) e em ``tests/fakes`` (memória). Todo método
levanta EXCEÇÕES DO DOMÍNIO (o adapter converte erros do SDK -> RawError -> mapeador).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, BinaryIO, Optional, Protocol, Sequence, Union, runtime_checkable

from bai_supabase.contracts.query import Filter, Sort


@dataclass(frozen=True)
class SelectRequest:
    table: str
    schema: str = "public"
    columns: Optional[tuple[str, ...]] = None
    filter: Optional[Filter] = None
    sorts: tuple[Sort, ...] = ()
    limit: Optional[int] = None
    offset: int = 0
    count: Optional[str] = None  # None | "exact" | "planned" | "estimated"


@dataclass(frozen=True)
class SelectResponse:
    rows: list[dict]
    count: Optional[int] = None


@runtime_checkable
class TableTransport(Protocol):
    def select(self, req: SelectRequest) -> SelectResponse: ...

    def insert(self, table: str, schema: str, rows: Sequence[dict]) -> list[dict]: ...

    def upsert(
        self,
        table: str,
        schema: str,
        rows: Sequence[dict],
        on_conflict: Optional[str] = None,
        ignore_duplicates: bool = False,
    ) -> list[dict]: ...

    def update(self, table: str, schema: str, changes: dict, filter: Filter) -> list[dict]: ...

    def delete(self, table: str, schema: str, filter: Filter) -> list[dict]: ...


@dataclass(frozen=True)
class TransportObject:
    path: str
    name: str
    size: Optional[int] = None
    content_type: Optional[str] = None
    updated_at: Optional[str] = None
    is_folder: bool = False


@runtime_checkable
class StorageTransport(Protocol):
    def upload_standard(
        self,
        bucket: str,
        path: str,
        data: Union[bytes, BinaryIO, str, Path],
        *,
        content_type: Optional[str] = None,
        upsert: bool = False,
        cache_control_seconds: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> None: ...

    def upload_resumable(
        self,
        bucket: str,
        path: str,
        source: Union[BinaryIO, str, Path],
        size: int,
        *,
        content_type: Optional[str] = None,
        upsert: bool = False,
        cache_control_seconds: Optional[int] = None,
        metadata: Optional[dict] = None,
        chunk_bytes: int = 6 * 1024 * 1024,
    ) -> None: ...

    def download_bytes(self, bucket: str, path: str) -> bytes: ...

    def download_to_file(self, bucket: str, path: str, destination: Path) -> Path: ...

    def create_signed_url(self, bucket: str, path: str, expires_in: int) -> str: ...

    def public_url(self, bucket: str, path: str) -> str: ...

    def exists(self, bucket: str, path: str) -> bool: ...

    def list_objects(
        self, bucket: str, prefix: str, limit: int, offset: int, sort_by: str = "name"
    ) -> list[TransportObject]: ...

    def remove(self, bucket: str, paths: Sequence[str]) -> list[str]:
        """Devolve os caminhos efetivamente removidos."""
        ...
