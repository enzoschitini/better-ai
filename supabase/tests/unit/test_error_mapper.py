"""Teste de TABELA do mapeador de erros (research/02 §5.2-§5.4, critério §14.3)."""
from __future__ import annotations

import pytest

from bai_supabase.errors import (
    AuthenticationError,
    ConfigurationError,
    ConflictError,
    DataError,
    DownloadError,
    DuplicateRecordError,
    FileAlreadyExistsError,
    FileNotFoundInStorageError,
    FileTooLargeError,
    OperationTimeoutError,
    PermissionDeniedError,
    RateLimitError,
    RawError,
    RecordNotFoundError,
    ReferenceViolationError,
    ServiceUnavailableError,
    SupabaseIntegrationError,
    UnexpectedError,
    UploadError,
    ValidationError,
    map_raw_error,
)

SECRET = "SEGREDO-PLANTADO-123"


def table(code=None, status=None, **kw) -> RawError:
    return RawError(origin="table", code=code, status=status, **kw)


def storage(code=None, status=None, **kw) -> RawError:
    return RawError(origin="storage", code=code, status=status, **kw)


def transport(kind) -> RawError:
    return RawError(origin="transport", transport_kind=kind)


# (raw, classe esperada, retryable esperado)
TABLE_CASES = [
    (table("23505", 409), DuplicateRecordError, False),
    (table("23503", 409), ReferenceViolationError, False),
    (table("23502", 400), DataError, False),
    (table("23514", 400), DataError, False),
    (table("22P02", 400), DataError, False),
    (table("22001", 400), DataError, False),
    (table("PGRST204", 400), DataError, False),
    (table("42501", 403), PermissionDeniedError, False),
    (table("42501", 401), PermissionDeniedError, False),  # PostgREST usa 401 para anon
    (table(None, 403), PermissionDeniedError, False),
    (table("PGRST301", 401), AuthenticationError, False),
    (table("PGRST302", 401), AuthenticationError, False),
    (table("PGRST303", 401), AuthenticationError, False),
    (table(None, 401), AuthenticationError, False),
    (table("42P01", 404), ConfigurationError, False),
    (table("PGRST205", 404), ConfigurationError, False),
    (table("PGRST202", 404), ConfigurationError, False),
    (table("PGRST000", 503), ServiceUnavailableError, True),
    (table("PGRST001", 503), ServiceUnavailableError, True),
    (table("PGRST002", 503), ServiceUnavailableError, True),
    (table("08006", 503), ServiceUnavailableError, True),
    (table("08001", None), ServiceUnavailableError, True),
    (table(None, 503), ServiceUnavailableError, True),
    (table("PGRST003", 504), OperationTimeoutError, True),
    (table(None, 504), OperationTimeoutError, True),
    (table("57014", 500), OperationTimeoutError, True),
    (table("53300", 503), ServiceUnavailableError, True),
    (table("53200", 500), ServiceUnavailableError, True),
    (table("40001", 409), ServiceUnavailableError, True),
    (table("40P01", 500), ServiceUnavailableError, True),
    (table(None, 429), RateLimitError, True),
    (table(None, 500), ServiceUnavailableError, True),
    (table("XX000", 502), ServiceUnavailableError, True),
    (table(None, 409), ConflictError, False),
    (table("PGRST100", 400), DataError, False),
    (table(None, 422), DataError, False),
    (table(None, 418), UnexpectedError, False),  # outro 4xx desconhecido
    (table("ZZZZZ", None), UnexpectedError, False),
    (table(), UnexpectedError, False),
]

STORAGE_CASES = [
    (storage("NoSuchKey", 404), FileNotFoundInStorageError, False),
    (storage("not_found", 404, message="Object not found"), FileNotFoundInStorageError, False),
    (storage(None, 404), FileNotFoundInStorageError, False),
    (storage("NoSuchBucket", 404), ConfigurationError, False),
    (storage("not_found", 404, message="Bucket not found"), ConfigurationError, False),
    (storage("Bucket not found", 404), ConfigurationError, False),
    (storage("ResourceAlreadyExists", 409), FileAlreadyExistsError, False),
    (storage("KeyAlreadyExists", 409), FileAlreadyExistsError, False),
    (storage("already_exists", 409), FileAlreadyExistsError, False),
    (storage("Duplicate", 409), FileAlreadyExistsError, False),
    (storage(None, 409), FileAlreadyExistsError, False),
    (storage("EntityTooLarge", 413), FileTooLargeError, False),
    (storage("Payload too large", 413), FileTooLargeError, False),
    (storage(None, 413), FileTooLargeError, False),
    (storage("InvalidMimeType", 415), ValidationError, False),
    (storage("InvalidKey", 400), ValidationError, False),
    (storage("InvalidBucketName", 400), ValidationError, False),
    (storage("InvalidRequest", 400), ValidationError, False),
    (storage("MissingParameter", 400), ValidationError, False),
    (storage(None, 400), ValidationError, False),
    (storage("AccessDenied", 403), PermissionDeniedError, False),
    (storage("unauthorized", 403), PermissionDeniedError, False),
    (storage(None, 403), PermissionDeniedError, False),
    (storage("InvalidJWT", 400), AuthenticationError, False),
    (storage("InvalidSignature", 400), AuthenticationError, False),
    (storage("SignatureDoesNotMatch", 403), AuthenticationError, False),
    (storage("unauthorized", 401), AuthenticationError, False),
    (storage(None, 401), AuthenticationError, False),
    (storage("InvalidChecksum", 400), UploadError, True),
    (storage("MissingPart", 400), UploadError, True),
    (storage("ResourceLocked", 423), ServiceUnavailableError, True),
    (storage("LockTimeout", 423), ServiceUnavailableError, True),
    (storage(None, 423), ServiceUnavailableError, True),
    (storage("DatabaseTimeout", 504), OperationTimeoutError, True),
    (storage("database_timeout", 504), OperationTimeoutError, True),
    (storage(None, 504), OperationTimeoutError, True),
    (storage(None, 544), OperationTimeoutError, True),
    (storage("SlowDown", 503), RateLimitError, True),
    (storage(None, 429), RateLimitError, True),
    (storage(None, 503), ServiceUnavailableError, True),
    (storage("InternalError", 500), ServiceUnavailableError, True),
    (storage("DatabaseError", 500), ServiceUnavailableError, True),
    (storage("internal_server_error", 500), ServiceUnavailableError, True),
    (storage(None, 500), ServiceUnavailableError, True),
    (storage("NovoCodigo", None), UnexpectedError, False),
    (storage(), UnexpectedError, False),
]

TRANSPORT_CASES = [
    (transport("timeout"), OperationTimeoutError, True),
    (transport("connect"), ServiceUnavailableError, True),
    (transport("decode"), ServiceUnavailableError, True),
    (transport("other"), UnexpectedError, False),
    (transport(None), UnexpectedError, False),
]


@pytest.mark.parametrize("raw, expected, retryable", TABLE_CASES + STORAGE_CASES + TRANSPORT_CASES)
def test_mapping_table(raw, expected, retryable):
    exc = map_raw_error(raw, operation="op.test", resource="recurso")
    assert type(exc) is expected
    assert exc.retryable is retryable
    assert exc.operation == "op.test"
    assert exc.resource == "recurso"
    assert exc.status == raw.status
    assert isinstance(exc, SupabaseIntegrationError)


@pytest.mark.parametrize(
    "details, expected",
    [
        ("The result contains 0 rows", RecordNotFoundError),
        ("The result contains 2 rows", DataError),
        ("The result contains 15 rows", DataError),
        (None, DataError),
    ],
)
def test_pgrst116_singular(details, expected):
    exc = map_raw_error(table("PGRST116", 406, details=details), operation="table.get")
    assert type(exc) is expected
    assert exc.retryable is False


def test_unmapped_is_unexpected_and_never_sdk_type():
    exc = map_raw_error(RawError(origin="storage", code="Zzz", exception_type="StorageApiError"), operation="storage.x")
    assert type(exc) is UnexpectedError
    assert "storage.x" in exc.message and "StorageApiError" in exc.message


def test_storage_other_http_status_depends_on_operation():
    assert type(map_raw_error(storage("Weird", 402), operation="storage.upload")) is UploadError
    assert type(map_raw_error(storage("Weird", 402), operation="storage.download")) is DownloadError
    assert type(map_raw_error(storage("Weird", 402), operation="storage.list")) is UnexpectedError


def test_storage_404_message_keeps_permission_caveat():
    exc = map_raw_error(storage("NoSuchKey", 404), operation="storage.download")
    assert "sem permissão" in exc.message


def test_rate_limit_carries_retry_after():
    exc = map_raw_error(table(None, 429, retry_after=7.5), operation="table.select")
    assert isinstance(exc, RateLimitError) and exc.retry_after == 7.5
    assert map_raw_error(table(None, 429), operation="t").retry_after is None
    assert map_raw_error(storage("SlowDown", 503, retry_after=-3.0), operation="s").retry_after == 0.0


def test_provider_code_and_correlation_id_are_filled():
    exc = map_raw_error(table("23505", 409), operation="table.insert", correlation_id="abc123")
    assert exc.provider_code == "23505" and exc.correlation_id == "abc123"
    assert "23505" in exc.message
    assert exc.outcome_unknown is False  # decidido só pelo executor


def test_raw_text_never_copied_into_exception():
    raw = table(
        "23505",
        409,
        message=f"duplicate key value {SECRET}",
        details=f"Key (email)=({SECRET}) already exists. contains 0 rows",
        hint=f"hint {SECRET}",
    )
    exc = map_raw_error(raw, operation="table.insert")
    dump = repr(exc.to_dict()) + str(exc) + repr(exc.args)
    assert SECRET not in dump


def test_unsafe_provider_code_is_dropped():
    exc = map_raw_error(table(f"23505 {SECRET}\n" + "x" * 100, 409), operation="t")
    assert exc.provider_code is None
    assert SECRET not in str(exc)
    assert type(exc) is ConflictError  # código inválido ignorado; decide o status 409


def test_unexpected_type_name_must_be_identifier():
    exc = map_raw_error(RawError(origin="table", exception_type=f"x {SECRET}"), operation="t")
    assert SECRET not in exc.message


def test_storage_400_asset_already_exists_vira_file_already_exists():
    """Docs (resumable uploads): objeto existente sem x-upsert => 400 'Asset Already Exists'."""
    from bai_supabase.errors import FileAlreadyExistsError, RawError, map_raw_error

    raw = RawError(origin="storage", status=400, code=None, message="Asset Already Exists")
    assert isinstance(map_raw_error(raw, operation="storage.upload"), FileAlreadyExistsError)


def test_storage_download_404_bucket_not_found_e_objeto_inexistente():
    """Quirk real (smoke): baixar objeto inexistente em bucket existente devolve 404 'Bucket not found'."""
    from bai_supabase.errors import ConfigurationError, FileNotFoundInStorageError, RawError, map_raw_error

    raw = RawError(origin="storage", status=404, code="Bucket not found", message="Bucket not found")
    assert isinstance(map_raw_error(raw, operation="storage.download"), FileNotFoundInStorageError)
    # em operação de listagem/upload continua sendo bucket inexistente
    assert isinstance(map_raw_error(raw, operation="storage.list"), ConfigurationError)
