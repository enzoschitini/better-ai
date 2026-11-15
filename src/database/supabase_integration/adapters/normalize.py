"""Fronteira de erros do adapter: exceção do SDK -> ``RawError`` -> exceção do domínio.

Este módulo (junto com os demais de ``adapters/``) é o ÚNICO autorizado a importar
``postgrest``, ``storage3`` e ``httpx`` (constituição P4). A decisão é por ATRIBUTOS
(``code``, ``status``, ``details``...) e por ``isinstance`` quando as classes existem;
nunca pelo NOME da classe. Todo adapter deve usar ``sdk_errors`` em volta de TODA
chamada ao SDK; a causa original fica em ``__cause__``.

Segurança: ``details``/``hint``/``message`` brutos só viajam dentro do ``RawError`` (interno,
truncado); o mapeador não os copia para a exceção do domínio.
"""

from __future__ import annotations

import json
import re
from contextlib import contextmanager
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Iterator, Optional

from src.database.supabase_integration.errors.exceptions import SupabaseIntegrationError
from src.database.supabase_integration.errors.mapper import map_raw_error
from src.database.supabase_integration.errors.raw import RawError

try:  # as classes são usadas só para isinstance; a decisão principal é por atributos
    import httpx
except ImportError:  # pragma: no cover - SDK sempre instalado no projeto
    httpx = None  # type: ignore[assignment]
try:
    from postgrest.exceptions import APIError as _PostgrestAPIError
except ImportError:  # pragma: no cover
    _PostgrestAPIError = None  # type: ignore[assignment,misc]
try:
    from storage3.exceptions import StorageApiError as _StorageApiError
    from storage3.utils import StorageException as _StorageException
except ImportError:  # pragma: no cover
    _StorageApiError = None  # type: ignore[assignment,misc]
    _StorageException = None  # type: ignore[assignment,misc]

_VALID_ORIGINS = ("table", "storage", "transport")
_MAX_TEXT = 500
_CAUSE_DEPTH = 5
_HTTP_STATUS = re.compile(r"^[1-5][0-9]{2}$")


# --------------------------------------------------------------------------- helpers
def _isinstance(exc: BaseException, cls: Optional[type]) -> bool:
    return cls is not None and isinstance(exc, cls)


def _httpx_isinstance(exc: BaseException, *names: str) -> bool:
    if httpx is None:
        return False
    return any(isinstance(exc, getattr(httpx, name)) for name in names if hasattr(httpx, name))


def _clip(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value)
    return text if len(text) <= _MAX_TEXT else text[:_MAX_TEXT] + "…"


def _to_status(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if 100 <= value <= 599 else None
    if isinstance(value, str) and _HTTP_STATUS.match(value.strip()):
        return int(value.strip())
    return None


def _causes(exc: BaseException) -> Iterator[BaseException]:
    """A própria exceção e sua cadeia ``__cause__``/``__context__`` (profundidade limitada)."""
    seen: set[int] = set()
    stack: list[Optional[BaseException]] = [exc]
    while stack and len(seen) < _CAUSE_DEPTH:
        current = stack.pop(0)
        if current is None or id(current) in seen:
            continue
        seen.add(id(current))
        yield current
        stack.extend([current.__cause__, current.__context__])


def _parse_retry_after(value: Any) -> Optional[float]:
    """Interpreta ``Retry-After`` (segundos ou data HTTP). Devolve segundos >= 0 ou None."""
    if value is None:
        return None
    text = str(value).strip()
    try:
        seconds = float(text)
    except ValueError:
        try:
            moment = parsedate_to_datetime(text)
        except (TypeError, ValueError):
            return None
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone.utc)
        seconds = (moment - datetime.now(timezone.utc)).total_seconds()
    if seconds != seconds or seconds in (float("inf"), float("-inf")):
        return None
    return max(0.0, seconds)


def _response_of(exc: BaseException) -> Any:
    for current in _causes(exc):
        response = getattr(current, "response", None)
        if response is not None and hasattr(response, "headers"):
            return response
    return None


def _retry_after_of(exc: BaseException) -> Optional[float]:
    response = _response_of(exc)
    if response is None:
        return None
    try:
        return _parse_retry_after(response.headers.get("retry-after"))
    except Exception:  # noqa: BLE001 - cabeçalho ilegível não pode mascarar o erro original
        return None


def _status_from_response(exc: BaseException) -> Optional[int]:
    response = _response_of(exc)
    return _to_status(getattr(response, "status_code", None)) if response is not None else None


def _name(exc: BaseException) -> str:
    return type(exc).__name__


# --------------------------------------------------------------------------- normalização
def _transport_kind(exc: BaseException) -> Optional[str]:
    """Classifica falhas de transporte; None se ``exc`` não for de transporte."""
    if _httpx_isinstance(exc, "TimeoutException") or isinstance(exc, TimeoutError):
        return "timeout"
    if _httpx_isinstance(exc, "NetworkError", "RemoteProtocolError", "ProxyError") or isinstance(
        exc, ConnectionError
    ):
        return "connect"
    if _httpx_isinstance(exc, "DecodingError") or isinstance(exc, (json.JSONDecodeError, UnicodeDecodeError)):
        return "decode"
    if _httpx_isinstance(exc, "TransportError"):
        return "other"
    return None


def _from_postgrest(exc: BaseException) -> RawError:
    raw_code = getattr(exc, "code", None)
    status = _to_status(raw_code) or _to_status(getattr(exc, "status", None)) or _status_from_response(exc)
    return RawError(
        origin="table",
        status=status,
        code=_clip(raw_code),
        message=_clip(getattr(exc, "message", None)),
        details=_clip(getattr(exc, "details", None)),
        hint=_clip(getattr(exc, "hint", None)),
        retry_after=_retry_after_of(exc),
        exception_type=_name(exc),
    )


def _from_storage(exc: BaseException) -> RawError:
    status = _to_status(getattr(exc, "status", None)) or _status_from_response(exc)
    return RawError(
        origin="storage",
        status=status,
        code=_clip(getattr(exc, "code", None)),
        message=_clip(getattr(exc, "message", None)),
        retry_after=_retry_after_of(exc),
        exception_type=_name(exc),
    )


def _from_http_status(exc: BaseException, origin: str) -> RawError:
    """``httpx.HTTPStatusError`` solto (sem a camada do SDK): usa só status e cabeçalhos."""
    return RawError(
        origin=origin,  # type: ignore[arg-type]
        status=_status_from_response(exc),
        retry_after=_retry_after_of(exc),
        exception_type=_name(exc),
    )


def _is_postgrest_like(exc: BaseException) -> bool:
    if _isinstance(exc, _PostgrestAPIError):
        return True
    return all(hasattr(exc, attr) for attr in ("code", "message", "details", "hint"))


def _is_storage_like(exc: BaseException) -> bool:
    if _isinstance(exc, _StorageException):
        return True
    return all(hasattr(exc, attr) for attr in ("code", "message", "status"))


def normalize_exception(exc: BaseException, *, origin: str = "transport") -> RawError:
    """Converte qualquer exceção do SDK/transporte em ``RawError`` (research/02 §5.1).

    ``origin`` ("table" | "storage") indica a frente da chamada e só é usado quando a exceção
    não revela a sua. Falhas de rede viram ``origin="transport"`` com ``transport_kind``.
    """
    origin = origin if origin in _VALID_ORIGINS else "transport"

    if _isinstance(exc, _PostgrestAPIError):
        return _from_postgrest(exc)
    if _isinstance(exc, _StorageException):
        return _from_storage(exc)

    kind = _transport_kind(exc)
    if kind is not None:
        return RawError(origin="transport", transport_kind=kind, exception_type=_name(exc))

    if _httpx_isinstance(exc, "HTTPStatusError"):
        return _from_http_status(exc, origin if origin != "transport" else "table")

    if _is_postgrest_like(exc):  # classes desconhecidas com o mesmo formato (outras versões)
        return _from_postgrest(exc)
    if _is_storage_like(exc):
        return _from_storage(exc)
    return RawError(origin=origin, exception_type=_name(exc))  # type: ignore[arg-type]


def map_exception(
    exc: BaseException, *, origin: str, operation: str, resource: Optional[str] = None
) -> SupabaseIntegrationError:
    """Exceção do SDK -> exceção do domínio (a causa é encadeada por quem levanta)."""
    if isinstance(exc, SupabaseIntegrationError):
        return exc
    raw = normalize_exception(exc, origin=origin)
    return map_raw_error(raw, operation=operation, resource=resource)


@contextmanager
def sdk_errors(origin: str, operation: str, resource: Optional[str] = None) -> Iterator[None]:
    """Contexto que traduz qualquer exceção do SDK para o domínio, preservando ``__cause__``."""
    try:
        yield
    except SupabaseIntegrationError:
        raise
    except Exception as exc:  # noqa: BLE001 - fronteira
        raise map_exception(exc, origin=origin, operation=operation, resource=resource) from exc
