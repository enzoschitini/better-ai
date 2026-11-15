"""Fontes de configuração (research/03 §3.3, §6 e §7).

ÚNICO módulo da integração que toca ``os.environ`` ou arquivos ``.env``. Nenhuma fonte
registra valores; o fallback legado registra apenas NOMES de variáveis.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

from src.database.supabase_integration.contracts.logging import LoggerContract

#: Mapa fixo do fallback legado (research/03 §6).
LEGACY_NAME_MAP: Mapping[str, str] = {
    "SBX_URL": "SUPABASE_URL",
    "SBX_SECRET_KEY": "SUPABASE_SECRET_KEY",
}

_LEGACY_FLAG = "SBX_ALLOW_LEGACY_FALLBACK"
_TRUE = frozenset({"1", "true", "yes"})


@runtime_checkable
class SettingsSource(Protocol):
    """Origem de pares nome -> texto. ``None`` significa ausente."""

    def get(self, name: str) -> Optional[str]: ...


@runtime_checkable
class EnumerableSource(SettingsSource, Protocol):
    """Fonte que também lista seus nomes (usado para avisar variáveis desconhecidas)."""

    def names(self) -> Iterable[str]: ...


def no_color_requested(environ: Optional[Mapping[str, str]] = None) -> bool:
    """True se a convenção ``NO_COLOR`` (https://no-color.org) está ativa (definida e não vazia)."""
    env = os.environ if environ is None else environ
    return bool(env.get("NO_COLOR"))


class EnvironmentSource:
    """Lê do ambiente do processo (ou de um mapa injetado, nos testes)."""

    reads_files = False

    def __init__(self, environ: Optional[Mapping[str, str]] = None) -> None:
        self._environ = environ

    def _env(self) -> Mapping[str, str]:
        return os.environ if self._environ is None else self._environ

    def get(self, name: str) -> Optional[str]:
        return self._env().get(name)

    def names(self) -> Iterable[str]:
        return list(self._env().keys())


class DictSource:
    """Fonte em memória (testes). Valores não-str são ignorados."""

    reads_files = False

    def __init__(self, values: Optional[Mapping[str, str]] = None) -> None:
        self._values = {k: v for k, v in (values or {}).items() if isinstance(v, str)}

    def get(self, name: str) -> Optional[str]:
        return self._values.get(name)

    def names(self) -> Iterable[str]:
        return list(self._values)


def parse_dotenv(text: str) -> dict[str, str]:
    """Parser mínimo de ``.env``: ``NOME=valor``, ``export``, comentários e aspas simples/duplas."""
    result: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        name, sep, value = line.partition("=")
        name = name.strip()
        if not sep or not name or not name.replace("_", "").isalnum() or name[0].isdigit():
            continue
        result[name] = _parse_value(value.strip())
    return result


def _parse_value(value: str) -> str:
    if value[:1] in ("'", '"'):
        quote = value[0]
        end = value.find(quote, 1)
        if end > 0:
            return value[1:end]
        return value[1:]
    cut = value.find(" #")  # comentário inline só após espaço
    return (value[:cut] if cut >= 0 else value).strip()


class DotenvFileSource:
    """Lê um arquivo ``.env``. SÓ toca o disco na primeira consulta (carregamento preguiçoso).

    Arquivo inexistente equivale a fonte vazia. O loader proíbe esta fonte em homol/prod.
    """

    reads_files = True

    def __init__(self, path: str | os.PathLike[str] = ".env") -> None:
        self._path = Path(path)
        self._cache: Optional[dict[str, str]] = None

    def _values(self) -> dict[str, str]:
        if self._cache is None:
            try:
                self._cache = parse_dotenv(self._path.read_text(encoding="utf-8-sig"))
            except OSError:
                self._cache = {}
        return self._cache

    def get(self, name: str) -> Optional[str]:
        return self._values().get(name)

    def names(self) -> Iterable[str]:
        return list(self._values())


class ChainedSource:
    """Consulta as fontes em ordem; a primeira com valor não vazio vence (research/03 §7)."""

    def __init__(self, *sources: SettingsSource) -> None:
        self._sources = sources

    @property
    def reads_files(self) -> bool:
        return any(getattr(s, "reads_files", False) for s in self._sources)

    @property
    def legacy_names_used(self) -> tuple[str, ...]:
        used: list[str] = []
        for source in self._sources:
            used.extend(getattr(source, "legacy_names_used", ()))
        return tuple(used)

    def get(self, name: str) -> Optional[str]:
        for source in self._sources:
            value = source.get(name)
            if value is not None and value.strip():
                return value
        return None

    def names(self) -> Iterable[str]:
        seen: dict[str, None] = {}
        for source in self._sources:
            for name in getattr(source, "names", lambda: ())():
                seen.setdefault(name, None)
        return list(seen)


class LegacyFallbackSource:
    """Decorador: se ``SBX_URL``/``SBX_SECRET_KEY`` faltarem, tenta o nome legado ``SUPABASE_*``.

    Desligado por padrão: ``enabled=None`` consulta ``SBX_ALLOW_LEGACY_FALLBACK`` na fonte
    interna. Só o NOME usado é registrado/exposto, nunca o valor. O loader proíbe o uso
    do fallback em homol/prod.
    """

    def __init__(
        self,
        inner: SettingsSource,
        *,
        enabled: Optional[bool] = None,
        mapping: Optional[Mapping[str, str]] = None,
        logger: Optional[LoggerContract] = None,
    ) -> None:
        self._inner = inner
        self._enabled = enabled
        self._mapping = dict(LEGACY_NAME_MAP if mapping is None else mapping)
        self._logger = logger
        self._used: list[str] = []

    @property
    def reads_files(self) -> bool:
        return bool(getattr(self._inner, "reads_files", False))

    @property
    def legacy_names_used(self) -> tuple[str, ...]:
        """Nomes SBX_* cujo valor veio do nome legado (sem valores)."""
        return tuple(self._used)

    def _is_enabled(self) -> bool:
        if self._enabled is not None:
            return self._enabled
        flag = self._inner.get(_LEGACY_FLAG)
        return flag is not None and flag.strip().lower() in _TRUE

    def get(self, name: str) -> Optional[str]:
        value = self._inner.get(name)
        if value is not None and value.strip():
            return value
        legacy = self._mapping.get(name)
        if legacy is None or not self._is_enabled():
            return value
        legacy_value = self._inner.get(legacy)
        if legacy_value is None or not legacy_value.strip():
            return value
        if name not in self._used:
            self._used.append(name)
            if self._logger is not None:
                self._logger.warning("fallback legado de configuração usado", variable=name, legacy_variable=legacy)
        return legacy_value

    def names(self) -> Iterable[str]:
        return list(getattr(self._inner, "names", lambda: ())())
