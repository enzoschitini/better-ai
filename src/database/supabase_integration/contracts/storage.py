"""Contratos da frente B (arquivos) — research/07."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import BinaryIO, Optional, Protocol, Sequence, Union, runtime_checkable

from src.database.supabase_integration.contracts.query import Page
from src.database.supabase_integration.contracts.results import DeleteReport, ObjectInfo, StoredFile


# --- Fontes de dados -------------------------------------------------------------
@dataclass(frozen=True)
class PathSource:
    path: Union[str, Path]
    filename: Optional[str] = None
    content_type: Optional[str] = None


@dataclass(frozen=True)
class BytesSource:
    data: bytes
    filename: Optional[str] = None
    content_type: Optional[str] = None


@dataclass(frozen=True)
class StreamSource:
    stream: BinaryIO
    size: Optional[int] = None  # tamanho conhecido (necessário para validar antes)
    filename: Optional[str] = None
    content_type: Optional[str] = None
    #: Se False, a fonte não pode ser relida do início => sem retry (research/02 §7.2).
    restartable: bool = False


FileSource = Union[PathSource, BytesSource, StreamSource]


class CollisionPolicy(str, Enum):
    REJECT = "reject"  # padrão: FileAlreadyExistsError
    VERSION = "version"  # grava em caminho novo (sufixo de versão)
    OVERWRITE = "overwrite"  # só explícito


@dataclass(frozen=True)
class UploadOptions:
    bucket: Optional[str] = None  # None = bucket padrão
    folder: Optional[str] = None  # subpasta lógica (ex.: domínio/owner)
    #: Caminho explícito (substitui a estratégia de nomeação). Sempre sanitizado.
    path: Optional[str] = None
    collision: CollisionPolicy = CollisionPolicy.REJECT
    content_type: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    cache_control_seconds: Optional[int] = None
    correlation_id: Optional[str] = None


@runtime_checkable
class NamingStrategy(Protocol):
    """Decide o caminho do objeto (injetável). Padrão: data + UUID."""

    def build_path(self, *, filename: Optional[str], folder: Optional[str], content_type: Optional[str]) -> str: ...


@runtime_checkable
class FileStore(Protocol):
    """Classe de arquivos. Todas as operações levantam exceções do domínio."""

    def upload(self, source: FileSource, options: Optional[UploadOptions] = None) -> StoredFile: ...

    def download(self, path: str, bucket: Optional[str] = None) -> bytes: ...

    def download_to(self, path: str, destination: Union[str, Path], bucket: Optional[str] = None) -> Path: ...

    def signed_url(self, path: str, bucket: Optional[str] = None, ttl_seconds: Optional[int] = None) -> str:
        """TTL limitado ao teto configurado; ``ValidationError`` acima dele."""
        ...

    def public_url(self, path: str, bucket: Optional[str] = None) -> str:
        """``ValidationError`` se o bucket não estiver declarado como público."""
        ...

    def exists(self, path: str, bucket: Optional[str] = None) -> bool: ...

    def list(
        self,
        prefix: str = "",
        bucket: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> Page[ObjectInfo]: ...

    def delete(self, paths: Sequence[str], bucket: Optional[str] = None) -> DeleteReport:
        """Idempotente: inexistente conta como removido/ausente, sem erro."""
        ...

    def delete_prefix(self, prefix: str, bucket: Optional[str] = None) -> DeleteReport: ...
