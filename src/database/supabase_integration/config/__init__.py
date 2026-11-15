"""Configuração centralizada: fontes, objeto imutável e loader com validação agregada."""

from src.database.supabase_integration.config.loader import SettingsLoader  # noqa: F401
from src.database.supabase_integration.config.settings import SupabaseSettings  # noqa: F401
from src.database.supabase_integration.config.sources import (  # noqa: F401
    ChainedSource,
    DictSource,
    DotenvFileSource,
    EnumerableSource,
    EnvironmentSource,
    LegacyFallbackSource,
    SettingsSource,
    no_color_requested,
)

__all__ = [
    "ChainedSource", "DictSource", "DotenvFileSource", "EnumerableSource", "EnvironmentSource",
    "LegacyFallbackSource", "SettingsLoader", "SettingsSource", "SupabaseSettings",
    "no_color_requested",
]
