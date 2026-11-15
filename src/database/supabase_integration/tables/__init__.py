"""Frente A: tabelas. Depende só de ``contracts``, ``errors`` e do logger injetado."""

from src.database.supabase_integration.tables.batch import BatchRunner  # noqa: F401
from src.database.supabase_integration.tables.pagination import KEYSET_START, Paginator  # noqa: F401
from src.database.supabase_integration.tables.repository import PostgresTableRepository  # noqa: F401
from src.database.supabase_integration.tables.serialization import EntityCodec, entity_kind, to_wire_value  # noqa: F401
from src.database.supabase_integration.tables.service import SupabaseTables  # noqa: F401
from src.database.supabase_integration.tables.validation import (  # noqa: F401
    TableValidator,
    ensure_table_allowed,
    validate_descriptor,
    validate_identifier,
)

__all__ = [
    "BatchRunner",
    "EntityCodec",
    "KEYSET_START",
    "Paginator",
    "PostgresTableRepository",
    "SupabaseTables",
    "TableValidator",
    "ensure_table_allowed",
    "entity_kind",
    "to_wire_value",
    "validate_descriptor",
    "validate_identifier",
]
