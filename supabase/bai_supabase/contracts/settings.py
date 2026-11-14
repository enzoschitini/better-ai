"""Fatias de configuração (research/03 §3.2).

As FATIAS vivem em ``contracts`` para que tabelas/arquivos dependam só de contratos.
O carregamento/validação a partir do ambiente fica em ``bai_supabase.config``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from bai_supabase.contracts.secret import Secret

MiB = 1024 * 1024


@dataclass(frozen=True)
class ConnectionSettings:
    url: str = ""
    secret_key: Secret = field(default_factory=lambda: Secret(""), repr=False)
    publishable_key: Optional[Secret] = field(default=None, repr=False)
    schema: str = "public"
    http_timeout_seconds: float = 10.0
    connect_timeout_seconds: float = 3.0
    retry_max_attempts: int = 3  # TOTAL de tentativas (1 = sem retry) — decisão C-4
    retry_backoff_base_seconds: float = 0.5
    retry_backoff_max_seconds: float = 8.0
    retry_budget_seconds: float = 30.0


@dataclass(frozen=True)
class TablesSettings:
    allowlist: tuple[str, ...] = ()  # vazio = qualquer tabela (obrigatória em prod)
    default_page_size: int = 50
    max_page_size: int = 1000
    batch_size: int = 500
    server_max_rows: int = 1000
    query_timeout_seconds: float = 10.0
    batch_timeout_seconds: float = 60.0


@dataclass(frozen=True)
class StorageSettings:
    default_bucket: Optional[str] = None
    buckets_allowlist: tuple[str, ...] = ()  # vazio = só o bucket padrão
    buckets_public: tuple[str, ...] = ()
    max_file_bytes: int = 50 * MiB
    allowed_mime: tuple[str, ...] = ()  # vazio = qualquer; aceita curinga "image/*"
    signed_url_ttl_seconds: int = 300  # decisão C-3
    signed_url_max_ttl_seconds: int = 3600
    upload_timeout_seconds: float = 120.0
    upsert_default: bool = False
    cache_control_seconds: int = 3600
    resumable_threshold_bytes: int = 6 * MiB
    resumable_chunk_bytes: int = 6 * MiB
    memory_cap_bytes: int = 32 * MiB
    list_page_size: int = 100
    delete_batch_size: int = 100
    max_concurrent_transfers: int = 4


@dataclass(frozen=True)
class LoggingSettings:
    level: str = "INFO"  # DEBUG | INFO | WARNING | ERROR
    color: str = "auto"  # auto | on | off
    format: str = "pretty"  # pretty | json
    slow_ms: int = 1000
    max_field_chars: int = 200


@dataclass(frozen=True)
class EnvironmentSettings:
    env: str = "dev"  # dev | homol | prod
    expected_project_ref: Optional[str] = None
    allow_legacy_fallback: bool = False
