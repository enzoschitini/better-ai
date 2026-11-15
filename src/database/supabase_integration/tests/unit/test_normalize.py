"""Normalização de exceções do SDK/transporte -> domínio (research/02 §5.1)."""
from __future__ import annotations

import json

import httpx
import pytest
from postgrest.exceptions import APIError
from storage3.exceptions import StorageApiError
from storage3.utils import StorageException

from src.database.supabase_integration.adapters.normalize import map_exception, normalize_exception, sdk_errors
from src.database.supabase_integration.errors import (
    AuthenticationError,
    DuplicateRecordError,
    FileAlreadyExistsError,
    FileNotFoundInStorageError,
    OperationTimeoutError,
    RateLimitError,
    RecordNotFoundError,
    ServiceUnavailableError,
    SupabaseIntegrationError,
    UnexpectedError,
)

SECRET = "SEGREDO-PLANTADO-123"
REQ = httpx.Request("GET", "https://proj.supabase.co/rest/v1/t")


def _status_error(status: int, headers: dict | None = None) -> httpx.HTTPStatusError:
    resp = httpx.Response(status, headers=headers or {}, request=REQ)
    return httpx.HTTPStatusError("falha", request=REQ, response=resp)


def _storage_error_with_cause(message, code, status, cause) -> StorageApiError:
    try:
        raise StorageApiError(message, code, status) from cause
    except StorageApiError as exc:  # noqa: PERF203
        return exc


# ------------------------------------------------------------------ PostgREST
def test_postgrest_api_error_is_normalized():
    exc = APIError({"message": "duplicate key", "code": "23505", "hint": "h", "details": "d"})
    raw = normalize_exception(exc, origin="table")
    assert (raw.origin, raw.code, raw.message, raw.hint, raw.details) == ("table", "23505", "duplicate key", "h", "d")
    assert raw.status is None
    assert raw.exception_type == "APIError"


def test_postgrest_default_error_with_http_status_code():
    exc = APIError({"message": "JSON could not be generated", "code": 502, "hint": None, "details": "b'...'"})
    raw = normalize_exception(exc, origin="table")
    assert raw.code == "502" and raw.status == 502


@pytest.mark.parametrize(
    "payload, expected",
    [
        ({"code": "23505", "message": "m"}, DuplicateRecordError),
        ({"code": "PGRST301", "message": "m"}, AuthenticationError),
        ({"code": "PGRST116", "message": "m", "details": "The result contains 0 rows"}, RecordNotFoundError),
        ({"code": 503, "message": "m"}, ServiceUnavailableError),
    ],
)
def test_postgrest_maps_to_domain(payload, expected):
    exc = map_exception(APIError(payload), origin="table", operation="table.select", resource="t")
    assert type(exc) is expected and exc.operation == "table.select" and exc.resource == "t"


def test_planted_secret_in_details_does_not_leak():
    err = APIError(
        {
            "code": "23505",
            "message": f"dup {SECRET}",
            "details": f"Key (email)=({SECRET}) already exists.",
            "hint": f"use {SECRET}",
        }
    )
    with pytest.raises(DuplicateRecordError) as info:
        with sdk_errors("table", "table.insert", "usuarios"):
            raise err
    domain = info.value
    assert SECRET not in (str(domain) + repr(domain.to_dict()) + repr(domain.args) + domain.message)
    assert domain.__cause__ is err  # causa preservada (só para depuração)


# ------------------------------------------------------------------ Storage
def test_storage_api_error_is_normalized():
    exc = StorageApiError("Object not found", "not_found", 404)
    raw = normalize_exception(exc, origin="storage")
    assert (raw.origin, raw.code, raw.status, raw.message) == ("storage", "not_found", 404, "Object not found")


def test_storage_status_as_string_is_converted():
    raw = normalize_exception(StorageApiError("x", "Duplicate", "409"), origin="storage")
    assert raw.status == 409


@pytest.mark.parametrize(
    "args, expected",
    [
        (("Object not found", "not_found", 404), FileNotFoundInStorageError),
        (("exists", "Duplicate", 409), FileAlreadyExistsError),
        (("jwt", "InvalidJWT", 400), AuthenticationError),
        (("slow", "SlowDown", 503), RateLimitError),
    ],
)
def test_storage_maps_to_domain(args, expected):
    exc = map_exception(StorageApiError(*args), origin="storage", operation="storage.download", resource="b/p")
    assert type(exc) is expected


def test_storage_exception_without_code_is_unexpected():
    exc = map_exception(StorageException("algo"), origin="storage", operation="storage.list")
    assert type(exc) is UnexpectedError and "StorageException" in exc.message


def test_retry_after_comes_from_cause_http_response():
    cause = _status_error(429, {"Retry-After": "12"})
    err = _storage_error_with_cause("slow", "SlowDown", 429, cause)
    raw = normalize_exception(err, origin="storage")
    assert raw.retry_after == 12.0
    mapped = map_exception(err, origin="storage", operation="storage.upload")
    assert isinstance(mapped, RateLimitError) and mapped.retry_after == 12.0


def test_retry_after_http_date_and_garbage():
    cause = _status_error(429, {"Retry-After": "Wed, 21 Oct 2015 07:28:00 GMT"})
    assert normalize_exception(_storage_error_with_cause("s", "SlowDown", 429, cause), origin="storage").retry_after == 0.0
    cause = _status_error(429, {"Retry-After": "daqui a pouco"})
    assert normalize_exception(_storage_error_with_cause("s", "SlowDown", 429, cause), origin="storage").retry_after is None


def test_bare_http_status_error_uses_response():
    raw = normalize_exception(_status_error(503, {"retry-after": "3"}), origin="storage")
    assert (raw.origin, raw.status, raw.retry_after) == ("storage", 503, 3.0)
    assert type(map_exception(_status_error(503), origin="table", operation="t")) is ServiceUnavailableError


# ------------------------------------------------------------------ transporte
@pytest.mark.parametrize(
    "exc, kind, expected",
    [
        (httpx.ReadTimeout("t", request=REQ), "timeout", OperationTimeoutError),
        (httpx.ConnectTimeout("t", request=REQ), "timeout", OperationTimeoutError),
        (httpx.PoolTimeout("t", request=REQ), "timeout", OperationTimeoutError),
        (httpx.ConnectError("c", request=REQ), "connect", ServiceUnavailableError),
        (httpx.ReadError("r", request=REQ), "connect", ServiceUnavailableError),
        (httpx.RemoteProtocolError("p", request=REQ), "connect", ServiceUnavailableError),
        (httpx.DecodingError("d", request=REQ), "decode", ServiceUnavailableError),
        (json.JSONDecodeError("bad", "{", 1), "decode", ServiceUnavailableError),
        (TimeoutError("t"), "timeout", OperationTimeoutError),
        (ConnectionResetError("c"), "connect", ServiceUnavailableError),
        (httpx.UnsupportedProtocol("u", request=REQ), "other", UnexpectedError),
    ],
)
def test_transport_errors(exc, kind, expected):
    raw = normalize_exception(exc, origin="table")
    assert raw.origin == "transport" and raw.transport_kind == kind
    assert type(map_exception(exc, origin="table", operation="table.select")) is expected


def test_unknown_exception_becomes_unexpected_with_type_name():
    exc = map_exception(KeyError("k"), origin="table", operation="table.select")
    assert type(exc) is UnexpectedError and "KeyError" in exc.message
    assert type(map_exception(RuntimeError("x"), origin="bogus", operation="o")) is UnexpectedError


# ------------------------------------------------------------------ sdk_errors
def test_sdk_errors_preserves_cause_and_domain_errors_pass_through():
    original = httpx.ReadTimeout("segredo " + SECRET, request=REQ)
    with pytest.raises(OperationTimeoutError) as info:
        with sdk_errors("table", "table.select", "t"):
            raise original
    assert info.value.__cause__ is original
    assert SECRET not in str(info.value)

    domain = ServiceUnavailableError("x")
    with pytest.raises(ServiceUnavailableError) as same:
        with sdk_errors("table", "table.select"):
            raise domain
    assert same.value is domain


def test_sdk_errors_never_leaks_sdk_types():
    for exc in (APIError({"code": "X"}), StorageApiError("m", "c", 400), httpx.ConnectError("c", request=REQ), OSError()):
        with pytest.raises(SupabaseIntegrationError):
            with sdk_errors("storage", "storage.x"):
                raise exc


def test_map_exception_returns_domain_error_as_is():
    err = UnexpectedError("x")
    assert map_exception(err, origin="table", operation="t") is err
