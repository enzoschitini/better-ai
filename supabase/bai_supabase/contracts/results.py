"""Objetos de resultado compartilhados."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from bai_supabase.errors.exceptions import SupabaseIntegrationError


@dataclass(frozen=True)
class DeleteResult:
    removed_count: int = 0

    @property
    def removed(self) -> bool:
        return self.removed_count > 0


@dataclass(frozen=True)
class ItemOutcome:
    index: int
    ok: bool
    entity: Any = None
    error: Optional[SupabaseIntegrationError] = None


@dataclass(frozen=True)
class BatchResult:
    items: list[ItemOutcome] = field(default_factory=list)
    stopped_early: bool = False

    @property
    def total(self) -> int:
        return len(self.items)

    @property
    def succeeded(self) -> int:
        return sum(1 for i in self.items if i.ok)

    @property
    def failed(self) -> int:
        return sum(1 for i in self.items if not i.ok)

    @property
    def all_ok(self) -> bool:
        return self.failed == 0 and not self.stopped_early


@dataclass(frozen=True)
class StoredFile:
    bucket: str
    path: str
    size: int
    content_type: Optional[str] = None
    original_name: Optional[str] = None
    upload_mode: str = "standard"  # standard | resumable
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ObjectInfo:
    path: str
    name: str
    size: Optional[int] = None
    content_type: Optional[str] = None
    updated_at: Optional[str] = None
    is_folder: bool = False


@dataclass(frozen=True)
class DeleteReport:
    requested: int = 0
    removed: list[str] = field(default_factory=list)
    failed: dict = field(default_factory=dict)  # path -> motivo (sem segredos)


class CompositeStatus(str, Enum):
    COMPLETA = "completa"
    PARCIAL = "parcial"
    FALHOU = "falhou"


@dataclass(frozen=True)
class CompositeResult:
    status: CompositeStatus
    steps_done: list[str] = field(default_factory=list)
    orphan_possible: bool = False
    correlation_id: Optional[str] = None
    record: Any = None
    stored_file: Optional[StoredFile] = None
    error: Optional[SupabaseIntegrationError] = None

    def raise_if_failed(self) -> "CompositeResult":
        """Levanta o MESMO objeto de exceção quando houve falha (``parcial`` ou ``falhou``)."""
        if self.error is not None:
            raise self.error
        return self
