"""Classe de arquivos: ``SupabaseStorage`` implementa ``FileStore`` (research/07, FR-B1..B8).

Depende só de contratos (transporte, executor, logger, configuração, nomeação), todos injetados.
O contrato é SÍNCRONO (decisão D-02): nunca chame dentro do event loop; use o wrapper assíncrono
por thread. Logs: sem conteúdo de arquivo e sem URL assinada.
"""

from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Optional, Protocol, Sequence, Union, runtime_checkable

from src.database.supabase_integration.contracts.logging import LoggerContract
from src.database.supabase_integration.contracts.query import Page
from src.database.supabase_integration.contracts.resilience import Operation, ResilienceExecutor
from src.database.supabase_integration.contracts.results import DeleteReport, ObjectInfo, StoredFile
from src.database.supabase_integration.contracts.settings import StorageSettings
from src.database.supabase_integration.contracts.storage import CollisionPolicy, FileSource, NamingStrategy, UploadOptions
from src.database.supabase_integration.contracts.transports import StorageTransport, TransportObject
from src.database.supabase_integration.errors.exceptions import (
    ConfigurationError,
    ConflictError,
    FileAlreadyExistsError,
    NotFoundError,
    OperationTimeoutError,
    ServiceUnavailableError,
    SupabaseIntegrationError,
    ValidationError,
)
from src.database.supabase_integration.storage.collision import CollisionResolver
from src.database.supabase_integration.storage.naming import DatedUuidNaming
from src.database.supabase_integration.storage.sources import PreparedSource, prepare_source
from src.database.supabase_integration.storage.validators import (
    FileValidator,
    sanitize_original_name,
    validate_object_path,
    validate_prefix,
)

MAX_LIST_LIMIT = 1000
MAX_METADATA_ENTRIES = 50
MAX_METADATA_VALUE_CHARS = 1024
MAX_VERSION_RACE_RETRIES = 3
MAX_PREFIX_DEPTH = 16
_DOWNLOAD_TTL = 60


@runtime_checkable
class SizedStorageTransport(Protocol):
    """Capacidade OPCIONAL do transporte: tamanho do objeto sem baixá-lo (teto de memória)."""

    def object_size(self, bucket: str, path: str) -> Optional[int]: ...


class SupabaseStorage:
    """Frente B: toda a manipulação de buckets, sem conhecer SDK nem tabelas."""

    def __init__(
        self,
        *,
        transport: StorageTransport,
        executor: ResilienceExecutor,
        logger: LoggerContract,
        settings: StorageSettings,
        naming: Optional[NamingStrategy] = None,
        validator: Optional[FileValidator] = None,
        clock: Any = time.perf_counter,
    ) -> None:
        if settings.max_concurrent_transfers < 1:
            raise ConfigurationError("max_concurrent_transfers deve ser >= 1", operation="storage.init")
        self._transport = transport
        self._executor = executor
        self._log = logger
        self._settings = settings
        self._naming = naming or DatedUuidNaming()
        self._validator = validator or FileValidator(settings)
        self._clock = clock
        self._transfers = threading.BoundedSemaphore(settings.max_concurrent_transfers)

    # ------------------------------------------------------------------ upload
    def upload(self, source: FileSource, options: Optional[UploadOptions] = None) -> StoredFile:
        opts = options or UploadOptions()
        fields: dict = {"correlation_id": opts.correlation_id}
        with self._guard("storage.upload", fields):
            bucket = fields["bucket"] = self._validator.resolve_bucket(opts.bucket)
            with prepare_source(
                source,
                max_bytes=self._settings.max_file_bytes,
                memory_cap_bytes=self._settings.memory_cap_bytes,
                spool_memory_bytes=self._settings.resumable_threshold_bytes,
            ) as prepared:
                self._validator.validate_size(prepared.size)
                content_type = self._validator.resolve_content_type(
                    filename=prepared.filename,
                    declared=opts.content_type or prepared.declared_content_type,
                    head=prepared.head,
                    public=self._validator.is_public(bucket),
                )
                base_path = self._build_path(opts, prepared, content_type)
                metadata = self._effective_metadata(opts, prepared)
                stored = self._transfer_with_collision(bucket, base_path, prepared, content_type, metadata, opts, fields)
            return stored

    def _build_path(self, opts: UploadOptions, prepared: PreparedSource, content_type: str) -> str:
        if opts.path:
            return validate_object_path(opts.path)
        return self._naming.build_path(filename=prepared.filename, folder=opts.folder, content_type=content_type)

    def _effective_metadata(self, opts: UploadOptions, prepared: PreparedSource) -> dict:
        metadata = dict(opts.metadata or {})
        if len(metadata) > MAX_METADATA_ENTRIES:
            raise ValidationError(f"metadados excedem {MAX_METADATA_ENTRIES} entradas", operation="storage.upload")
        for key, value in metadata.items():
            if not isinstance(key, str) or not isinstance(value, str) or len(value) > MAX_METADATA_VALUE_CHARS:
                raise ValidationError(
                    "metadados devem ser str -> str (valor até 1024 caracteres)", operation="storage.upload"
                )
        if prepared.filename:
            metadata["original_name"] = sanitize_original_name(prepared.filename)
        return metadata

    def _transfer_with_collision(
        self, bucket: str, base_path: str, prepared: PreparedSource, content_type: str,
        metadata: dict, opts: UploadOptions, fields: dict,
    ) -> StoredFile:
        resolver = CollisionResolver(lambda p: self._exists(bucket, p, opts.correlation_id))
        attempts = MAX_VERSION_RACE_RETRIES if opts.collision is CollisionPolicy.VERSION else 1
        for attempt in range(1, attempts + 1):
            resolution = resolver.resolve(base_path, opts.collision)
            fields["path"] = resolution.path
            if resolution.upsert:
                self._log.warning(
                    "storage.upload sobrescrevendo (upsert explícito)", operation="storage.upload",
                    bucket=bucket, path=resolution.path, correlation_id=opts.correlation_id,
                )
            try:
                return self._send(bucket, resolution.path, prepared, content_type, metadata, opts, resolution.upsert, fields)
            except FileAlreadyExistsError:
                if attempt >= attempts:
                    raise
        raise AssertionError("inalcançável")  # pragma: no cover

    def _send(
        self, bucket: str, path: str, prepared: PreparedSource, content_type: str, metadata: dict,
        opts: UploadOptions, upsert: bool, fields: dict,
    ) -> StoredFile:
        mode = "resumable" if prepared.size > self._settings.resumable_threshold_bytes else "standard"
        cache = opts.cache_control_seconds if opts.cache_control_seconds is not None else self._settings.cache_control_seconds
        operation = Operation(
            name="storage.upload", resource=f"{bucket}/{path}", idempotent=upsert, category="file_transfer",
            restartable=prepared.restartable, correlation_id=opts.correlation_id,
        )
        fields.update(size_bytes=prepared.size, mode=mode)

        def attempt() -> None:
            common = dict(content_type=content_type, upsert=upsert, cache_control_seconds=cache, metadata=metadata)
            if mode == "standard" and prepared.data is not None:
                self._transport.upload_standard(bucket, path, prepared.data, **common)
            elif mode == "standard":
                with prepared.open() as handle:
                    self._transport.upload_standard(bucket, path, handle, **common)
            else:
                with prepared.open() as handle:
                    self._transport.upload_resumable(
                        bucket, path, handle, prepared.size,
                        chunk_bytes=self._settings.resumable_chunk_bytes, **common,
                    )

        try:
            with self._transfers:
                self._executor.run(operation, attempt)
        except (OperationTimeoutError, ServiceUnavailableError) as exc:
            exc.outcome_unknown = True  # o objeto pode ter sido gravado: o backend deve conferir
            raise
        stored = StoredFile(
            bucket=bucket, path=path, size=prepared.size, content_type=content_type,
            original_name=metadata.get("original_name"), upload_mode=mode, metadata=dict(metadata),
        )
        self._info("storage.upload concluído", "storage.upload", fields)
        return stored

    # ---------------------------------------------------------------- download
    def download(self, path: str, bucket: Optional[str] = None) -> bytes:
        fields: dict = {}
        with self._guard("storage.download", fields):
            bucket = fields["bucket"] = self._validator.resolve_bucket(bucket)
            path = fields["path"] = validate_object_path(path)
            self._check_memory_cap(bucket, path)
            operation = Operation(
                name="storage.download", resource=f"{bucket}/{path}", idempotent=True, category="file_transfer"
            )
            with self._transfers:
                data = self._executor.run(operation, lambda: self._transport.download_bytes(bucket, path))
            if len(data) > self._settings.memory_cap_bytes:
                raise ValidationError(
                    "objeto excede o teto de memória; use download_to", operation="storage.download"
                )
            fields["size_bytes"] = len(data)
            self._info("storage.download concluído", "storage.download", fields)
            return data

    def _check_memory_cap(self, bucket: str, path: str) -> None:
        """Recusa antes de baixar quando o transporte sabe informar o tamanho."""
        if not isinstance(self._transport, SizedStorageTransport):
            return
        operation = Operation(name="storage.size", resource=f"{bucket}/{path}", idempotent=True, category="file_meta")
        size = self._executor.run(operation, lambda: self._transport.object_size(bucket, path))  # type: ignore[attr-defined]
        if size is not None and size > self._settings.memory_cap_bytes:
            raise ValidationError(
                f"objeto de {size} bytes excede o teto de memória ({self._settings.memory_cap_bytes}); use download_to",
                operation="storage.download",
            )

    def download_to(self, path: str, destination: Union[str, Path], bucket: Optional[str] = None) -> Path:
        fields: dict = {}
        with self._guard("storage.download_to", fields):
            bucket = fields["bucket"] = self._validator.resolve_bucket(bucket)
            path = fields["path"] = validate_object_path(path)
            target = Path(destination)
            target.parent.mkdir(parents=True, exist_ok=True)
            operation = Operation(
                name="storage.download_to", resource=f"{bucket}/{path}", idempotent=True, category="file_transfer"
            )
            with self._transfers:
                result = self._executor.run(operation, lambda: self._transport.download_to_file(bucket, path, target))
            fields["size_bytes"] = Path(result).stat().st_size if Path(result).exists() else None
            self._info("storage.download_to concluído", "storage.download_to", fields)
            return Path(result)

    # -------------------------------------------------------------------- URLs
    def signed_url(self, path: str, bucket: Optional[str] = None, ttl_seconds: Optional[int] = None) -> str:
        fields: dict = {}
        with self._guard("storage.signed_url", fields):
            bucket = fields["bucket"] = self._validator.resolve_bucket(bucket)
            path = fields["path"] = validate_object_path(path)
            ttl = self._settings.signed_url_ttl_seconds if ttl_seconds is None else ttl_seconds
            if isinstance(ttl, bool) or not isinstance(ttl, int) or ttl <= 0:
                raise ValidationError("TTL da URL assinada deve ser um inteiro positivo", operation="storage.signed_url")
            if ttl > self._settings.signed_url_max_ttl_seconds:
                raise ValidationError(
                    f"TTL de {ttl}s excede o teto de {self._settings.signed_url_max_ttl_seconds}s",
                    operation="storage.signed_url",
                )
            fields["ttl_seconds"] = ttl
            operation = Operation(
                name="storage.signed_url", resource=f"{bucket}/{path}", idempotent=True, category="file_meta"
            )
            url = self._executor.run(operation, lambda: self._transport.create_signed_url(bucket, path, ttl))
            self._info("storage.signed_url gerada", "storage.signed_url", fields)  # nunca loga a URL
            return url

    def public_url(self, path: str, bucket: Optional[str] = None) -> str:
        fields: dict = {}
        with self._guard("storage.public_url", fields):
            bucket = fields["bucket"] = self._validator.resolve_bucket(bucket)
            path = fields["path"] = validate_object_path(path)
            if not self._validator.is_public(bucket):
                raise ValidationError(
                    f"bucket {bucket!r} não está declarado como público; use signed_url", operation="storage.public_url"
                )
            return self._transport.public_url(bucket, path)  # montagem local, sem rede

    # ------------------------------------------------------------ exists / list
    def exists(self, path: str, bucket: Optional[str] = None) -> bool:
        fields: dict = {}
        with self._guard("storage.exists", fields):
            bucket = fields["bucket"] = self._validator.resolve_bucket(bucket)
            path = fields["path"] = validate_object_path(path)
            found = self._exists(bucket, path, None)
            fields["exists"] = found
            self._info("storage.exists concluído", "storage.exists", fields)
            return found

    def _exists(self, bucket: str, path: str, correlation_id: Optional[str]) -> bool:
        operation = Operation(
            name="storage.exists", resource=f"{bucket}/{path}", idempotent=True, category="file_meta",
            correlation_id=correlation_id,
        )
        return self._executor.run(operation, lambda: self._transport.exists(bucket, path))

    def list(self, prefix: str = "", bucket: Optional[str] = None, limit: Optional[int] = None, offset: int = 0) -> Page[ObjectInfo]:
        fields: dict = {}
        with self._guard("storage.list", fields):
            bucket = fields["bucket"] = self._validator.resolve_bucket(bucket)
            prefix = fields["prefix"] = validate_prefix(prefix)
            size = self._settings.list_page_size if limit is None else limit
            if isinstance(size, bool) or not isinstance(size, int) or not 0 < size <= MAX_LIST_LIMIT:
                raise ValidationError(f"limit deve estar entre 1 e {MAX_LIST_LIMIT}", operation="storage.list")
            if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
                raise ValidationError("offset deve ser >= 0", operation="storage.list")
            rows = self._list_raw(bucket, prefix, size + 1, offset)  # +1 revela se há próxima página
            page = Page(
                items=[self._to_info(r) for r in rows[:size]], limit=size, offset=offset, has_more=len(rows) > size
            )
            fields.update(count=len(page.items), has_more=page.has_more)
            self._info("storage.list concluído", "storage.list", fields)
            return page

    def _list_raw(self, bucket: str, prefix: str, limit: int, offset: int) -> list[TransportObject]:
        operation = Operation(
            name="storage.list", resource=f"{bucket}/{prefix}", idempotent=True, category="file_meta"
        )
        return self._executor.run(operation, lambda: self._transport.list_objects(bucket, prefix, limit, offset))

    @staticmethod
    def _to_info(row: TransportObject) -> ObjectInfo:
        return ObjectInfo(
            path=row.path, name=row.name, size=row.size, content_type=row.content_type,
            updated_at=row.updated_at, is_folder=row.is_folder,
        )

    # ------------------------------------------------------------------ delete
    def delete(self, paths: Sequence[str], bucket: Optional[str] = None) -> DeleteReport:
        fields: dict = {}
        with self._guard("storage.delete", fields):
            bucket = fields["bucket"] = self._validator.resolve_bucket(bucket)
            if isinstance(paths, (str, bytes)) or not paths:
                raise ValidationError("informe uma lista não vazia de caminhos", operation="storage.delete")
            unique = list(dict.fromkeys(validate_object_path(p) for p in paths))  # tudo validado antes da rede
            report = self._remove_batches(bucket, unique)
            fields.update(requested=report.requested, removed=len(report.removed), failed=len(report.failed))
            self._info("storage.delete concluído", "storage.delete", fields)
            return report

    def _remove_batches(self, bucket: str, paths: list[str]) -> DeleteReport:
        removed: list[str] = []
        failed: dict = {}
        step = max(1, self._settings.delete_batch_size)
        for start in range(0, len(paths), step):
            batch = paths[start : start + step]
            operation = Operation(
                name="storage.delete", resource=f"{bucket}[{len(batch)} objetos]", idempotent=True, category="file_meta"
            )
            try:
                removed.extend(self._executor.run(operation, lambda b=batch: self._transport.remove(bucket, b)))
            except SupabaseIntegrationError as exc:  # um lote ruim não aborta os demais
                self._log_failure("storage.delete lote falhou", "storage.delete", exc, {"bucket": bucket, "batch_size": len(batch)})
                reason = f"{type(exc).__name__}: {exc.message}"
                failed.update({p: reason for p in batch})
        return DeleteReport(requested=len(paths), removed=removed, failed=failed)

    def delete_prefix(self, prefix: str, bucket: Optional[str] = None) -> DeleteReport:
        fields: dict = {}
        with self._guard("storage.delete_prefix", fields):
            bucket = fields["bucket"] = self._validator.resolve_bucket(bucket)
            prefix = fields["prefix"] = validate_prefix(prefix, allow_empty=False)
            self._log.warning(
                "storage.delete_prefix operação destrutiva", operation="storage.delete_prefix", bucket=bucket, prefix=prefix
            )
            requested = 0
            removed: list[str] = []
            failed: dict = {}
            stack = [(prefix, 0)]
            while stack:
                current, depth = stack.pop()
                files, folders = self._list_everything(bucket, current)
                if folders and depth + 1 > MAX_PREFIX_DEPTH:
                    raise ValidationError("prefixo excede a profundidade máxima de varredura", operation="storage.delete_prefix")
                stack.extend((f"{current}/{name}", depth + 1) for name in folders)
                if files:
                    part = self._remove_batches(bucket, files)
                    requested += part.requested
                    removed.extend(part.removed)
                    failed.update(part.failed)
            report = DeleteReport(requested=requested, removed=removed, failed=failed)
            fields.update(requested=requested, removed=len(removed), failed=len(failed))
            self._info("storage.delete_prefix concluído", "storage.delete_prefix", fields)
            return report

    def _list_everything(self, bucket: str, prefix: str) -> tuple[list[str], list[str]]:
        """Lista (paginando) uma pasta; devolve (caminhos de arquivos, nomes de subpastas)."""
        files: list[str] = []
        folders: list[str] = []
        page_size = max(1, min(self._settings.list_page_size, MAX_LIST_LIMIT))
        offset = 0
        while True:
            rows = self._list_raw(bucket, prefix, page_size, offset)
            for row in rows:
                (folders if row.is_folder else files).append(row.name if row.is_folder else f"{prefix}/{row.name}")
            if len(rows) < page_size:
                return files, folders
            offset += page_size

    # ----------------------------------------------------------------- logging
    @contextmanager
    def _guard(self, operation: str, fields: dict) -> Iterator[None]:
        """Registra a falha UMA vez (na fronteira) e a repropaga com a mesma identidade."""
        started = self._clock()
        fields["_started"] = started
        try:
            yield
        except SupabaseIntegrationError as exc:
            self._log_failure(f"{operation} falhou", operation, exc, fields)
            raise

    def _elapsed_ms(self, fields: dict) -> int:
        return int((self._clock() - fields.get("_started", self._clock())) * 1000)

    def _public_fields(self, fields: dict) -> dict:
        return {k: v for k, v in fields.items() if not k.startswith("_") and v is not None}

    def _info(self, event: str, operation: str, fields: dict) -> None:
        self._log.info(event, operation=operation, duration_ms=self._elapsed_ms(fields), **self._public_fields(fields))

    def _log_failure(self, event: str, operation: str, exc: SupabaseIntegrationError, fields: dict) -> None:
        expected = isinstance(exc, (ValidationError, ConflictError, NotFoundError))
        emit = self._log.warning if expected else self._log.error
        emit(
            event, operation=operation, duration_ms=self._elapsed_ms(fields), exception_class=type(exc).__name__,
            retryable=exc.retryable, status=exc.status, outcome_unknown=exc.outcome_unknown,
            **self._public_fields(fields),
        )
