"""Frente B: classe de arquivos (research/07). Depende só de contratos e erros."""

from src.database.supabase_integration.storage.collision import CollisionResolver, Resolution, versioned_path  # noqa: F401
from src.database.supabase_integration.storage.naming import DatedUuidNaming, PreservedNameNaming  # noqa: F401
from src.database.supabase_integration.storage.service import SizedStorageTransport, SupabaseStorage  # noqa: F401
from src.database.supabase_integration.storage.sources import PreparedSource, prepare_source  # noqa: F401
from src.database.supabase_integration.storage.validators import (  # noqa: F401
    FileValidator,
    extension_of,
    is_mime_allowed,
    sanitize_original_name,
    slugify_filename,
    validate_object_path,
    validate_prefix,
    validate_size,
)

__all__ = [
    "CollisionResolver",
    "DatedUuidNaming",
    "FileValidator",
    "PreparedSource",
    "PreservedNameNaming",
    "Resolution",
    "SizedStorageTransport",
    "SupabaseStorage",
    "extension_of",
    "is_mime_allowed",
    "prepare_source",
    "sanitize_original_name",
    "slugify_filename",
    "validate_object_path",
    "validate_prefix",
    "validate_size",
    "versioned_path",
]
