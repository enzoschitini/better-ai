"""Frente A: tabelas. Depende só de ``contracts``, ``errors`` e do logger injetado."""

from bai_supabase.tables.batch import BatchRunner  # noqa: F401
from bai_supabase.tables.pagination import KEYSET_START, Paginator  # noqa: F401
from bai_supabase.tables.repository import PostgresTableRepository  # noqa: F401
from bai_supabase.tables.serialization import EntityCodec, entity_kind, to_wire_value  # noqa: F401
from bai_supabase.tables.service import SupabaseTables  # noqa: F401
from bai_supabase.tables.validation import (  # noqa: F401
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
