"""``SettingsLoader``: lê, converte, valida e agrega erros (research/03 §3-§7, §12).

Falha cedo com UM ``SettingsError`` listando TODOS os ausentes/inválidos: só NOMES e a
regra violada, nunca valores. Não lê ambiente diretamente: recebe uma ``SettingsSource``.
"""

from __future__ import annotations

import re
from typing import Any, Optional
from urllib.parse import urlsplit

from src.database.supabase_integration.config.settings import SupabaseSettings
from src.database.supabase_integration.config.sources import SettingsSource
from src.database.supabase_integration.contracts.logging import LoggerContract
from src.database.supabase_integration.contracts.secret import Secret
from src.database.supabase_integration.contracts.settings import (
    ConnectionSettings,
    EnvironmentSettings,
    LoggingSettings,
    StorageSettings,
    TablesSettings,
)
from src.database.supabase_integration.errors import SettingsError

PREFIX = "SBX_"
DOC_PATH = "src/database/supabase_integration/docs/spec/research/01-variaveis-de-ambiente.md"
EXAMPLE_PATH = "src/database/supabase_integration/.env.example"

#: Fonte da verdade dos nomes lidos (espelhada em ``src/database/supabase_integration/.env.example``).
VARIABLE_NAMES: tuple[str, ...] = (
    # ambiente e conexão
    "SBX_ENV", "SBX_URL", "SBX_SECRET_KEY", "SBX_PUBLISHABLE_KEY", "SBX_DB_SCHEMA",
    "SBX_DB_CONNECTION_STRING", "SBX_HTTP_TIMEOUT_SECONDS", "SBX_HTTP_CONNECT_TIMEOUT_SECONDS",
    "SBX_RETRY_MAX_ATTEMPTS", "SBX_RETRY_BACKOFF_BASE_SECONDS", "SBX_RETRY_BACKOFF_MAX_SECONDS",
    "SBX_RETRY_BUDGET_SECONDS", "SBX_EXPECTED_PROJECT_REF", "SBX_ALLOW_LEGACY_FALLBACK",
    # tabelas
    "SBX_TABLES_ALLOWLIST", "SBX_TABLES_DEFAULT_PAGE_SIZE", "SBX_TABLES_MAX_PAGE_SIZE",
    "SBX_TABLES_BATCH_SIZE", "SBX_TABLES_SERVER_MAX_ROWS", "SBX_TABLES_QUERY_TIMEOUT_SECONDS",
    "SBX_TABLES_BATCH_TIMEOUT_SECONDS",
    # arquivos
    "SBX_BUCKET_DEFAULT", "SBX_BUCKETS_ALLOWLIST", "SBX_BUCKETS_PUBLIC", "SBX_STORAGE_MAX_FILE_BYTES",
    "SBX_STORAGE_ALLOWED_MIME", "SBX_STORAGE_SIGNED_URL_TTL_SECONDS",
    "SBX_STORAGE_SIGNED_URL_MAX_TTL_SECONDS", "SBX_STORAGE_UPLOAD_TIMEOUT_SECONDS",
    "SBX_STORAGE_UPSERT_DEFAULT", "SBX_STORAGE_CACHE_CONTROL_SECONDS",
    "SBX_STORAGE_RESUMABLE_THRESHOLD_BYTES", "SBX_STORAGE_RESUMABLE_CHUNK_BYTES",
    "SBX_STORAGE_MEMORY_CAP_BYTES", "SBX_STORAGE_LIST_PAGE_SIZE", "SBX_STORAGE_DELETE_BATCH_SIZE",
    "SBX_STORAGE_MAX_CONCURRENT_TRANSFERS",
    # log
    "SBX_LOG_LEVEL", "SBX_LOG_COLOR", "SBX_LOG_FORMAT", "SBX_LOG_SLOW_MS", "SBX_LOG_MAX_FIELD_CHARS",
)
_KNOWN = frozenset(VARIABLE_NAMES)

#: Padrões por ambiente (research/03 §7): (nível, cor, formato).
_ENV_LOG_DEFAULTS = {
    "dev": ("DEBUG", "auto", "pretty"),
    "homol": ("INFO", "auto", "pretty"),
    "prod": ("WARNING", "off", "json"),
}
_ENVS = tuple(_ENV_LOG_DEFAULTS)
_STRICT_ENVS = ("homol", "prod")
_LOOPBACK = frozenset({"localhost", "127.0.0.1", "::1"})

_INT_RE = re.compile(r"[+-]?[0-9]+")
_FLOAT_RE = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
_TRUE = frozenset({"true", "1", "yes"})
_FALSE = frozenset({"false", "0", "no"})
_TABLE_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,62}")
_BUCKET_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}")
_MIME_RE = re.compile(r"[a-z0-9!#$&^_.+-]+/(?:[a-z0-9!#$&^_.+-]+|\*)")
_REF_RE = re.compile(r"[a-z0-9][a-z0-9-]{1,62}")

_D_CONN, _D_TABLES, _D_STORAGE, _D_LOG = ConnectionSettings(), TablesSettings(), StorageSettings(), LoggingSettings()


def _fmt(number: float) -> str:
    return f"{number:g}"


class _Reader:
    """Lê variáveis conhecidas, converte e acumula erros. Valor inválido devolve ``None``."""

    def __init__(self, source: SettingsSource) -> None:
        self._source = source
        self.missing: list[str] = []
        self.invalid: list[tuple[str, str]] = []
        self.read: set[str] = set()

    def fail(self, name: str, reason: str) -> None:
        if (name, reason) not in self.invalid:
            self.invalid.append((name, reason))

    def need(self, name: str) -> None:
        if name not in self.missing:
            self.missing.append(name)

    def raw(self, name: str) -> Optional[str]:
        assert name in _KNOWN, f"variável não registrada em VARIABLE_NAMES: {name}"
        self.read.add(name)
        value = self._source.get(name)
        value = value.strip() if isinstance(value, str) else ""
        return value or None  # vazio conta como ausente

    def text(self, name: str, *, default: Any = None, required: bool = False,
             pattern: Optional[re.Pattern] = None, rule: str = "formato inválido", lower: bool = False) -> Any:
        value = self.raw(name)
        if value is None:
            if required:
                self.need(name)
            return default
        value = value.lower() if lower else value
        if pattern is not None and not pattern.fullmatch(value):
            self.fail(name, rule)
            return None
        return value

    def integer(self, name: str, default: int, minimum: int, maximum: Optional[int] = None) -> Optional[int]:
        value = self.raw(name)
        if value is None:
            return default
        rule = f"deve ser inteiro >= {minimum}" + (f" e <= {maximum}" if maximum is not None else "")
        if not _INT_RE.fullmatch(value):
            self.fail(name, rule)
            return None
        number = int(value)
        if number < minimum or (maximum is not None and number > maximum):
            self.fail(name, rule)
            return None
        return number

    def number(self, name: str, default: float, minimum: float, *, strict: bool = True) -> Optional[float]:
        value = self.raw(name)
        if value is None:
            return default
        rule = f"deve ser número {'>' if strict else '>='} {_fmt(minimum)}"
        if not _FLOAT_RE.fullmatch(value):
            self.fail(name, rule)
            return None
        number = float(value)
        if number == float("inf") or (number <= minimum if strict else number < minimum):
            self.fail(name, rule)
            return None
        return number

    def boolean(self, name: str, default: bool) -> Optional[bool]:
        value = self.raw(name)
        if value is None:
            return default
        low = value.lower()
        if low in _TRUE:
            return True
        if low in _FALSE:
            return False
        self.fail(name, "deve ser booleano (true/false/1/0/yes/no)")
        return None

    def choice(self, name: str, choices: tuple[str, ...], default: Optional[str], *, upper: bool = False) -> Optional[str]:
        value = self.raw(name)
        if value is None:
            return default
        value = value.upper() if upper else value.lower()
        if value not in choices:
            self.fail(name, f"deve ser um de {', '.join(choices)}")
            return None
        return value

    def items(self, name: str, pattern: re.Pattern, rule: str, *, lower: bool = False) -> Optional[tuple[str, ...]]:
        value = self.raw(name)
        if value is None:
            return ()
        found: dict[str, None] = {}
        for part in value.split(","):
            part = part.strip()
            if not part:
                continue
            part = part.lower() if lower else part
            if not pattern.fullmatch(part):
                self.fail(name, rule)
                return None
            found.setdefault(part, None)
        return tuple(found)

    def secret(self, name: str, *, required: bool = False, forbidden_prefix: str = "", forbidden_rule: str = "") -> Optional[Secret]:
        value = self.raw(name)
        if value is None:
            if required:
                self.need(name)
            return None
        if forbidden_prefix and value.startswith(forbidden_prefix):
            self.fail(name, forbidden_rule)
            return None
        return Secret(value)


def _parse_url(reader: _Reader, name: str, env: str) -> Optional[str]:
    value = reader.raw(name)
    if value is None:
        reader.need(name)
        return None
    rule = "deve ser URL https válida" + (" (http só para localhost em dev)" if env == "dev" else "")
    try:
        parts = urlsplit(value)
        host = parts.hostname
        port_ok = parts.port is None or parts.port > 0
    except ValueError:
        reader.fail(name, rule)
        return None
    loopback_http = parts.scheme == "http" and env == "dev" and host in _LOOPBACK
    if (parts.scheme != "https" and not loopback_http) or not host or not port_ok:
        reader.fail(name, rule)
        return None
    if parts.username or parts.password or parts.query or parts.fragment:
        reader.fail(name, "não deve conter credenciais, query ou fragmento")
        return None
    return value.rstrip("/")


def _project_ref(url: str) -> str:
    return (urlsplit(url).hostname or "").split(".")[0].lower()


class SettingsLoader:
    """Carrega ``SupabaseSettings`` de uma ``SettingsSource``. Reutilizável; sem estado global."""

    def __init__(self, logger: Optional[LoggerContract] = None) -> None:
        self._logger = logger
        self._warnings: list[str] = []

    @staticmethod
    def variable_names() -> tuple[str, ...]:
        """Todos os nomes de variáveis lidos (usado no teste de consistência do ``.env.example``)."""
        return VARIABLE_NAMES

    @property
    def warnings(self) -> list[str]:
        """Avisos do último ``load`` (só nomes de variáveis)."""
        return list(self._warnings)

    def _warn(self, message: str) -> None:
        self._warnings.append(message)
        if self._logger is not None:
            self._logger.warning(message)

    def load(self, source: SettingsSource) -> SupabaseSettings:
        self._warnings = []
        self._warn_unknown(source)
        reader = _Reader(source)
        env_name = reader.choice("SBX_ENV", _ENVS, "dev")
        env = env_name or "dev"

        connection = self._connection(reader, env)
        tables = self._tables(reader, env_name)
        storage = self._storage(reader, env_name)
        logging_ = self._logging(reader, env)
        environment = self._environment(reader, source, env_name, connection)

        if reader.missing or reader.invalid:
            raise self._error(reader, env_name)
        assert reader.read == _KNOWN, "loader deixou de ler alguma variável registrada"
        return SupabaseSettings(connection, tables, storage, logging_, environment)

    # --- fatias -------------------------------------------------------------------
    def _connection(self, r: _Reader, env: str) -> ConnectionSettings:
        d = _D_CONN
        url = _parse_url(r, "SBX_URL", env)
        secret = r.secret("SBX_SECRET_KEY", required=True, forbidden_prefix="sb_publishable_",
                          forbidden_rule="parece chave publishable; use a chave secret")
        publishable = r.secret("SBX_PUBLISHABLE_KEY", forbidden_prefix="sb_secret_",
                               forbidden_rule="parece chave secret; use a chave publishable")
        schema = r.text("SBX_DB_SCHEMA", default=d.schema, pattern=_TABLE_RE, rule="deve ser identificador SQL simples")
        if r.raw("SBX_DB_CONNECTION_STRING") is not None:
            self._warn("SBX_DB_CONNECTION_STRING definida, mas reservada e ignorada na v1")
        timeout = r.number("SBX_HTTP_TIMEOUT_SECONDS", d.http_timeout_seconds, 0)
        connect = r.number("SBX_HTTP_CONNECT_TIMEOUT_SECONDS", d.connect_timeout_seconds, 0)
        attempts = r.integer("SBX_RETRY_MAX_ATTEMPTS", d.retry_max_attempts, 1)
        base = r.number("SBX_RETRY_BACKOFF_BASE_SECONDS", d.retry_backoff_base_seconds, 0)
        cap = r.number("SBX_RETRY_BACKOFF_MAX_SECONDS", d.retry_backoff_max_seconds, 0)
        budget = r.number("SBX_RETRY_BUDGET_SECONDS", d.retry_budget_seconds, 0)
        if base is not None and cap is not None and cap < base:
            r.fail("SBX_RETRY_BACKOFF_MAX_SECONDS", "deve ser >= SBX_RETRY_BACKOFF_BASE_SECONDS")
        return ConnectionSettings(
            url=url or "", secret_key=secret or Secret(""), publishable_key=publishable,
            schema=schema or d.schema, http_timeout_seconds=timeout or d.http_timeout_seconds,
            connect_timeout_seconds=connect or d.connect_timeout_seconds,
            retry_max_attempts=attempts or d.retry_max_attempts,
            retry_backoff_base_seconds=base or d.retry_backoff_base_seconds,
            retry_backoff_max_seconds=cap or d.retry_backoff_max_seconds,
            retry_budget_seconds=budget or d.retry_budget_seconds,
        )

    def _tables(self, r: _Reader, env: Optional[str]) -> TablesSettings:
        d = _D_TABLES
        allow = r.items("SBX_TABLES_ALLOWLIST", _TABLE_RE, "deve ser lista de nomes de tabela simples")
        server_rows = r.integer("SBX_TABLES_SERVER_MAX_ROWS", d.server_max_rows, 1)
        max_default = min(d.max_page_size, server_rows) if server_rows else d.max_page_size
        max_page = r.integer("SBX_TABLES_MAX_PAGE_SIZE", max_default, 1)
        page_default = min(d.default_page_size, max_page) if max_page else d.default_page_size
        page = r.integer("SBX_TABLES_DEFAULT_PAGE_SIZE", page_default, 1)
        batch = r.integer("SBX_TABLES_BATCH_SIZE", d.batch_size, 1)
        query_timeout = r.number("SBX_TABLES_QUERY_TIMEOUT_SECONDS", d.query_timeout_seconds, 0)
        batch_timeout = r.number("SBX_TABLES_BATCH_TIMEOUT_SECONDS", d.batch_timeout_seconds, 0)
        if max_page and server_rows and max_page > server_rows:
            r.fail("SBX_TABLES_MAX_PAGE_SIZE", "deve ser <= SBX_TABLES_SERVER_MAX_ROWS")
        if page and max_page and page > max_page:
            r.fail("SBX_TABLES_DEFAULT_PAGE_SIZE", "deve ser <= SBX_TABLES_MAX_PAGE_SIZE")
        self._require_allowlist(r, env, "SBX_TABLES_ALLOWLIST", allow)
        return TablesSettings(
            allowlist=allow or (), default_page_size=page or d.default_page_size,
            max_page_size=max_page or d.max_page_size, batch_size=batch or d.batch_size,
            server_max_rows=server_rows or d.server_max_rows,
            query_timeout_seconds=query_timeout or d.query_timeout_seconds,
            batch_timeout_seconds=batch_timeout or d.batch_timeout_seconds,
        )

    def _storage(self, r: _Reader, env: Optional[str]) -> StorageSettings:
        d = _D_STORAGE
        bucket_rule = "deve ser lista de nomes de bucket simples"
        default_bucket = r.text("SBX_BUCKET_DEFAULT", pattern=_BUCKET_RE, rule="deve ser nome de bucket simples")
        allow = r.items("SBX_BUCKETS_ALLOWLIST", _BUCKET_RE, bucket_rule)
        public = r.items("SBX_BUCKETS_PUBLIC", _BUCKET_RE, bucket_rule)
        mime = r.items("SBX_STORAGE_ALLOWED_MIME", _MIME_RE, "deve ser lista de tipos MIME (aceita image/*)", lower=True)
        max_bytes = r.integer("SBX_STORAGE_MAX_FILE_BYTES", d.max_file_bytes, 1)
        ttl = r.integer("SBX_STORAGE_SIGNED_URL_TTL_SECONDS", d.signed_url_ttl_seconds, 1)
        ttl_max = r.integer("SBX_STORAGE_SIGNED_URL_MAX_TTL_SECONDS", d.signed_url_max_ttl_seconds, 1)
        upload_timeout = r.number("SBX_STORAGE_UPLOAD_TIMEOUT_SECONDS", d.upload_timeout_seconds, 0)
        upsert = r.boolean("SBX_STORAGE_UPSERT_DEFAULT", d.upsert_default)
        cache = r.integer("SBX_STORAGE_CACHE_CONTROL_SECONDS", d.cache_control_seconds, 0)
        threshold = r.integer("SBX_STORAGE_RESUMABLE_THRESHOLD_BYTES", d.resumable_threshold_bytes, 1)
        chunk = r.integer("SBX_STORAGE_RESUMABLE_CHUNK_BYTES", d.resumable_chunk_bytes, 1)
        memory = r.integer("SBX_STORAGE_MEMORY_CAP_BYTES", d.memory_cap_bytes, 1)
        list_page = r.integer("SBX_STORAGE_LIST_PAGE_SIZE", d.list_page_size, 1)
        delete_batch = r.integer("SBX_STORAGE_DELETE_BATCH_SIZE", d.delete_batch_size, 1)
        concurrency = r.integer("SBX_STORAGE_MAX_CONCURRENT_TRANSFERS", d.max_concurrent_transfers, 1)
        if ttl and ttl_max and ttl > ttl_max:
            r.fail("SBX_STORAGE_SIGNED_URL_TTL_SECONDS", "deve ser <= SBX_STORAGE_SIGNED_URL_MAX_TTL_SECONDS")
        if allow and default_bucket and default_bucket not in allow:
            r.fail("SBX_BUCKET_DEFAULT", "deve constar em SBX_BUCKETS_ALLOWLIST")
        self._require_allowlist(r, env, "SBX_BUCKETS_ALLOWLIST", allow)
        return StorageSettings(
            default_bucket=default_bucket, buckets_allowlist=allow or (), buckets_public=public or (),
            max_file_bytes=max_bytes or d.max_file_bytes, allowed_mime=mime or (),
            signed_url_ttl_seconds=ttl or d.signed_url_ttl_seconds,
            signed_url_max_ttl_seconds=ttl_max or d.signed_url_max_ttl_seconds,
            upload_timeout_seconds=upload_timeout or d.upload_timeout_seconds,
            upsert_default=d.upsert_default if upsert is None else upsert,
            cache_control_seconds=d.cache_control_seconds if cache is None else cache,
            resumable_threshold_bytes=threshold or d.resumable_threshold_bytes,
            resumable_chunk_bytes=chunk or d.resumable_chunk_bytes,
            memory_cap_bytes=memory or d.memory_cap_bytes,
            list_page_size=list_page or d.list_page_size,
            delete_batch_size=delete_batch or d.delete_batch_size,
            max_concurrent_transfers=concurrency or d.max_concurrent_transfers,
        )

    def _logging(self, r: _Reader, env: str) -> LoggingSettings:
        level_d, color_d, format_d = _ENV_LOG_DEFAULTS[env]
        level = r.choice("SBX_LOG_LEVEL", ("DEBUG", "INFO", "WARNING", "ERROR"), level_d, upper=True)
        color = r.choice("SBX_LOG_COLOR", ("auto", "on", "off"), color_d)
        fmt = r.choice("SBX_LOG_FORMAT", ("pretty", "json"), format_d)
        slow = r.integer("SBX_LOG_SLOW_MS", _D_LOG.slow_ms, 0)
        max_chars = r.integer("SBX_LOG_MAX_FIELD_CHARS", _D_LOG.max_field_chars, 20)
        return LoggingSettings(
            level=level or level_d, color=color or color_d, format=fmt or format_d,
            slow_ms=_D_LOG.slow_ms if slow is None else slow, max_field_chars=max_chars or _D_LOG.max_field_chars,
        )

    def _environment(self, r: _Reader, source: SettingsSource, env: Optional[str],
                     connection: ConnectionSettings) -> EnvironmentSettings:
        ref = r.text("SBX_EXPECTED_PROJECT_REF", pattern=_REF_RE, rule="deve ser identificador de projeto (minúsculas/números)", lower=True)
        allow_legacy = r.boolean("SBX_ALLOW_LEGACY_FALLBACK", False)
        if ref and connection.url and ref != _project_ref(connection.url):
            r.fail("SBX_EXPECTED_PROJECT_REF", "não corresponde ao projeto de SBX_URL")
        if env in _STRICT_ENVS:
            if allow_legacy:
                r.fail("SBX_ALLOW_LEGACY_FALLBACK", "proibido em homol/prod")
            for name in getattr(source, "legacy_names_used", ()):
                r.fail(name, "valor obtido por fallback legado, proibido em homol/prod")
            if getattr(source, "reads_files", False):
                r.fail("SBX_ENV", ".env de arquivo não é permitido em homol/prod; use variáveis da plataforma")
        return EnvironmentSettings(env=env or "dev", expected_project_ref=ref, allow_legacy_fallback=bool(allow_legacy))

    # --- regras auxiliares ----------------------------------------------------------
    def _require_allowlist(self, r: _Reader, env: Optional[str], name: str, value: Optional[tuple[str, ...]]) -> None:
        if value is None:  # já inválida
            return
        if not value and env == "prod":
            r.need(name)
        elif not value and env == "homol":
            self._warn(f"{name} recomendada em homol")

    def _warn_unknown(self, source: SettingsSource) -> None:
        names = getattr(source, "names", None)
        if names is None:
            return
        for name in sorted(set(names())):
            if name.startswith(PREFIX) and not name.startswith("SBX_TEST_") and name not in _KNOWN:
                self._warn(f"variável desconhecida (erro de digitação?): {name}")

    def _error(self, r: _Reader, env: Optional[str]) -> SettingsError:
        lines = [f"configuração do Supabase inválida (ambiente: {env or 'indefinido'})"]
        if r.missing:
            lines.append("  Ausentes (obrigatórias):")
            lines.extend(f"    - {name}" for name in r.missing)
        if r.invalid:
            lines.append("  Inválidas:")
            lines.extend(f"    - {name}: {reason}" for name, reason in r.invalid)
        lines.append(f"  Ver: {DOC_PATH} e {EXAMPLE_PATH}")
        return SettingsError("\n".join(lines), operation="load_settings", missing=r.missing, invalid=r.invalid)
