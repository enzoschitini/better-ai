"""Resolução de colisão de caminho (research/07 §7, decisão A-08).

- ``REJECT``: não consulta nada; o servidor recusa (409) e o adapter levanta ``FileAlreadyExistsError``
  de forma atômica (sem corrida entre "existe?" e "grava").
- ``VERSION``: procura o primeiro sufixo ``-vN`` livre (preserva o objeto antigo; evita cache de CDN).
- ``OVERWRITE``: upsert explícito (quem chama registra o aviso).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from bai_supabase.contracts.storage import CollisionPolicy
from bai_supabase.errors.exceptions import FileAlreadyExistsError, ValidationError

MAX_VERSIONS = 1000
_VERSION_SUFFIX = re.compile(r"-v\d+$")


@dataclass(frozen=True)
class Resolution:
    path: str
    upsert: bool = False
    versioned: bool = False


def versioned_path(path: str, version: int) -> str:
    """``a/b/c.mp4`` + 3 -> ``a/b/c-v3.mp4`` (substitui um sufixo ``-vN`` anterior)."""
    folder, slash, name = path.rpartition("/")
    stem, dot, ext = name.rpartition(".")
    if not dot:
        stem, ext = name, ""
    stem = _VERSION_SUFFIX.sub("", stem)
    return f"{folder}{slash}{stem}-v{version}{dot}{ext}"


class CollisionResolver:
    """Resolve o caminho final conforme a política; ``exists`` é injetado (sem conhecer transporte)."""

    def __init__(self, exists: Callable[[str], bool], *, max_versions: int = MAX_VERSIONS) -> None:
        self._exists = exists
        self._max_versions = max_versions

    def resolve(self, path: str, policy: CollisionPolicy) -> Resolution:
        if policy is CollisionPolicy.OVERWRITE:
            return Resolution(path, upsert=True)
        if policy is CollisionPolicy.REJECT:
            return Resolution(path)
        if policy is CollisionPolicy.VERSION:
            return self._next_version(path)
        raise ValidationError(f"política de colisão desconhecida: {policy!r}", operation="storage.collision")

    def _next_version(self, path: str) -> Resolution:
        if not self._exists(path):
            return Resolution(path)
        for version in range(2, self._max_versions + 1):
            candidate = versioned_path(path, version)
            if not self._exists(candidate):
                return Resolution(candidate, versioned=True)
        raise FileAlreadyExistsError(
            f"sem versão livre após {self._max_versions} tentativas", operation="storage.collision"
        )
