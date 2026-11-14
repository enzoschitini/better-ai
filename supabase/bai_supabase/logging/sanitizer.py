"""Sanitizador único (função pura) aplicado antes de qualquer log (research/02 §10.3, 05 §3 e §9).

Mascara chaves, JWTs, cabeçalhos, URLs assinadas, strings de conexão, senhas e e-mails;
remove valores de linhas do Postgres; trunca textos longos. A redação acontece ANTES
da formatação, então cor/JSON não conseguem contorná-la.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Mapping
from typing import Any

from bai_supabase.contracts.secret import Secret

MASK = "***"

#: Menor tamanho de segredo extra mascarado por busca literal (evita estragar o texto).
_MIN_EXTRA_SECRET_LEN = 4
_MAX_DEPTH = 6
_MAX_ITEMS = 50

#: Chaves de campo cujo valor é sempre mascarado (comparação sem caixa, ``-`` == ``_``).
_SENSITIVE_KEYS = frozenset(
    {
        "apikey", "api_key", "x_api_key", "authorization", "proxy_authorization",
        "token", "access_token", "refresh_token", "id_token", "secret", "secret_key",
        "password", "passwd", "pwd", "senha", "cookie", "set_cookie", "signature",
        "service_role", "service_role_key", "publishable_key", "connection_string",
        "db_connection_string", "dsn", "signed_url", "signedurl",
    }
)
_SENSITIVE_SUFFIXES = ("_token", "_secret", "_password", "_apikey", "_api_key", "_secret_key")

_QUERY_KEYS = (
    "token|access_token|refresh_token|id_token|apikey|api_key|key|signature|sig|password|secret"
    "|x-amz-signature|x-amz-credential|x-amz-security-token"
)

_URL_RE = re.compile(r"https?://[^\s\"'<>)\]]+", re.IGNORECASE)
_CONN_RE = re.compile(
    r"\b(postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqps?)://[^\s\"']+", re.IGNORECASE
)
_JWT_RE = re.compile(r"(?<![A-Za-z0-9_-])eyJ[A-Za-z0-9_-]{8,}(?:\.[A-Za-z0-9_-]*){0,2}")
_SB_KEY_RE = re.compile(r"\bsb_(?:secret|publishable)_[A-Za-z0-9_-]+")
_BEARER_RE = re.compile(r"\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{6,}", re.IGNORECASE)
_KV_RE = re.compile(
    r"(?<![A-Za-z0-9])((?:password|passwd|pwd|senha|secret_key|secret|access_token|refresh_token|id_token"
    r"|token|api[-_]?key|authorization|proxy-authorization|cookie|connection_string)"
    r"[\"']?\s*[:=]\s*[\"']?)(?:(?:bearer|basic)\s+)?[^\s\"',;&}\]]+",
    re.IGNORECASE,
)
_QUERY_PARAM_RE = re.compile(rf"([?&#;](?:{_QUERY_KEYS})=)[^&\s\"'#]+", re.IGNORECASE)
_FAILING_ROW_RE = re.compile(r"Failing row contains \((?:.*\)|.*)", re.IGNORECASE)
_PG_KEY_RE = re.compile(r"\bKey \(([^)]*)\)=\(.*?\)(?=\s|\.|$)")
_EMAIL_RE = re.compile(r"\b([A-Za-z0-9])[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")


def _is_sensitive_key(key: Any) -> bool:
    norm = str(key).strip().lower().replace("-", "_").replace(" ", "_")
    return norm in _SENSITIVE_KEYS or norm.endswith(_SENSITIVE_SUFFIXES)


def _mask_url(match: re.Match) -> str:
    """Remove credenciais da URL e a query de URLs assinadas (``/sign/``)."""
    scheme, _, rest = match.group(0).partition("://")
    cut = min((i for i in (rest.find("/"), rest.find("?"), rest.find("#")) if i >= 0), default=len(rest))
    authority, tail = rest[:cut], rest[cut:]
    if "@" in authority:
        authority = f"{MASK}@{authority.rsplit('@', 1)[1]}"
    path, sep, _query = tail.partition("?")
    if sep and "/sign/" in path:
        tail = f"{path}?{MASK}"
    return f"{scheme}://{authority}{tail}"


def _mask_text(text: str, extra: tuple[str, ...]) -> str:
    for secret in extra:
        text = text.replace(secret, MASK)
    text = _CONN_RE.sub(lambda m: f"{m.group(1)}://{MASK}", text)
    text = _URL_RE.sub(_mask_url, text)
    text = _JWT_RE.sub(MASK, text)
    text = _SB_KEY_RE.sub(MASK, text)
    text = _BEARER_RE.sub(lambda m: f"{m.group(1)} {MASK}", text)
    text = _KV_RE.sub(lambda m: f"{m.group(1)}{MASK}", text)
    text = _QUERY_PARAM_RE.sub(lambda m: f"{m.group(1)}{MASK}", text)
    text = _FAILING_ROW_RE.sub(f"Failing row contains ({MASK})", text)
    text = _PG_KEY_RE.sub(lambda m: f"Key ({m.group(1)})=({MASK})", text)
    return _EMAIL_RE.sub(lambda m: f"{m.group(1)}{MASK}@{m.group(2)}", text)


def _truncate(text: str, max_chars: int) -> str:
    if max_chars > 0 and len(text) > max_chars:
        return f"{text[:max_chars]}…[+{len(text) - max_chars} chars]"
    return text


def _normalize_extra(extra_secrets: Iterable[Any]) -> tuple[str, ...]:
    found: set[str] = set()
    for item in extra_secrets or ():
        value = item.reveal() if isinstance(item, Secret) else item
        if isinstance(value, str) and len(value) >= _MIN_EXTRA_SECRET_LEN:
            found.add(value)
    return tuple(sorted(found, key=len, reverse=True))


def _walk(value: Any, max_chars: int, extra: tuple[str, ...], depth: int) -> Any:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, Secret):
        return MASK
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    if isinstance(value, str):
        return _truncate(_mask_text(value, extra), max_chars)
    if isinstance(value, (bytes, bytearray, memoryview)):
        return f"<{len(value)} bytes>"  # conteúdo binário nunca vai para o log
    if isinstance(value, BaseException):
        return _truncate(_mask_text(f"{type(value).__name__}: {value}", extra), max_chars)
    if depth >= _MAX_DEPTH:
        return "<...>"
    if isinstance(value, Mapping):
        return _walk_mapping(value, max_chars, extra, depth)
    if isinstance(value, (list, tuple, set, frozenset)):
        items = list(value)
        out = [_walk(v, max_chars, extra, depth + 1) for v in items[:_MAX_ITEMS]]
        if len(items) > _MAX_ITEMS:
            out.append(f"…[+{len(items) - _MAX_ITEMS} items]")
        return out
    return _truncate(_mask_text(str(value), extra), max_chars)


def _walk_mapping(value: Mapping, max_chars: int, extra: tuple[str, ...], depth: int) -> dict:
    out: dict[str, Any] = {}
    for index, (key, item) in enumerate(value.items()):
        if index >= _MAX_ITEMS:
            out["…"] = f"+{len(value) - _MAX_ITEMS} items"
            break
        name = _truncate(_mask_text(str(key), extra), 100)
        out[name] = MASK if _is_sensitive_key(key) else _walk(item, max_chars, extra, depth + 1)
    return out


def sanitize(value: Any, *, max_chars: int = 200, extra_secrets: Iterable[Any] = ()) -> Any:
    """Devolve ``value`` seguro e serializável em JSON (str/num/bool/None/list/dict).

    ``max_chars <= 0`` desliga o truncamento. ``extra_secrets`` aceita ``str``/``Secret``
    (valores com menos de 4 caracteres são ignorados).
    """
    return _walk(value, max_chars, _normalize_extra(extra_secrets), 0)


def sanitize_fields(
    fields: Mapping[str, Any], *, max_chars: int = 200, extra_secrets: Iterable[Any] = ()
) -> dict[str, Any]:
    """Sanitiza um dicionário de campos de log (chaves sensíveis ficam ``***``)."""
    return _walk_mapping(fields, max_chars, _normalize_extra(extra_secrets), 0)
