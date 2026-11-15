"""Estratégias de nomeação do objeto (research/07 §6). Implementam ``NamingStrategy``.

O nome original do usuário NUNCA vai para o caminho de ``DatedUuidNaming``: vai como metadado.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Callable, Optional

from src.database.supabase_integration.errors.exceptions import ValidationError
from src.database.supabase_integration.storage.validators import (
    extension_for_mime,
    extension_of,
    slugify_filename,
    validate_object_path,
    validate_prefix,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _join(*parts: str) -> str:
    return "/".join(p for p in parts if p)


class DatedUuidNaming:
    """Padrão: ``<folder>/<AAAA>/<MM>/<uuid><ext>`` (nunca colide; pastas pequenas)."""

    def __init__(
        self,
        clock: Callable[[], datetime] = _utc_now,
        uuid_factory: Callable[[], uuid.UUID] = uuid.uuid4,
    ) -> None:
        self._clock = clock
        self._uuid = uuid_factory

    def build_path(self, *, filename: Optional[str], folder: Optional[str], content_type: Optional[str]) -> str:
        now = self._clock()
        ext = extension_of(filename) or extension_for_mime(content_type)
        name = f"{self._uuid()}{ext}"
        return validate_object_path(_join(validate_prefix(folder), f"{now:%Y}", f"{now:%m}", name))


class PreservedNameNaming:
    """``<folder>/<nome-saneado>``: mantém o nome (sem acentos/espaços). Pode colidir: use ``CollisionPolicy``."""

    def build_path(self, *, filename: Optional[str], folder: Optional[str], content_type: Optional[str]) -> str:
        if not filename:
            raise ValidationError("nome do arquivo é obrigatório para esta estratégia", operation="storage.naming")
        name = slugify_filename(filename)
        if not extension_of(name) and extension_for_mime(content_type):
            name += extension_for_mime(content_type)
        return validate_object_path(_join(validate_prefix(folder), name))
