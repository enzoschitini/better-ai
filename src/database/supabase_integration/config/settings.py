"""``SupabaseSettings``: objeto raiz imutável que compõe as fatias (research/03 §3).

Só dados: não lê ambiente nem rede. ``repr``/``str``/``safe_summary`` nunca expõem valores.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any

from src.database.supabase_integration.contracts.secret import Secret
from src.database.supabase_integration.contracts.settings import (
    ConnectionSettings,
    EnvironmentSettings,
    LoggingSettings,
    StorageSettings,
    TablesSettings,
)

DEFINED = "definido"
UNDEFINED = "não definido"

_SLICES = ("connection", "tables", "storage", "logging", "environment")


def _state(value: Any) -> str:
    if value is None or value == "" or value == ():
        return UNDEFINED
    if isinstance(value, Secret) and not value:
        return UNDEFINED
    return DEFINED


@dataclass(frozen=True, repr=False)
class SupabaseSettings:
    """Configuração completa, congelada. Cada classe da integração recebe só a sua fatia."""

    connection: ConnectionSettings = field(default_factory=ConnectionSettings)
    tables: TablesSettings = field(default_factory=TablesSettings)
    storage: StorageSettings = field(default_factory=StorageSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    environment: EnvironmentSettings = field(default_factory=EnvironmentSettings)

    def safe_summary(self) -> dict[str, Any]:
        """Resumo para log: nomes de campos e ``definido``/``não definido``; nunca valores.

        Única exceção: ``env`` (dev/homol/prod), que não é sensível.
        """
        summary: dict[str, Any] = {"env": self.environment.env}
        for name in _SLICES:
            part = getattr(self, name)
            summary[name] = {f.name: _state(getattr(part, f.name)) for f in fields(part)}
        return summary

    def __repr__(self) -> str:
        conn = self.connection
        return (
            f"SupabaseSettings(env={self.environment.env!r}, url={_state(conn.url)!r}, "
            f"secret_key={'***' if conn.secret_key else _state(conn.secret_key)!r}, "
            f"log_level={self.logging.level!r})"
        )

    __str__ = __repr__
