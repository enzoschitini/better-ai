"""Mapeador puro: ``RawError`` -> exceção do domínio (research/02 §5.2, §5.3 e §5.4).

Função pura, sem I/O e sem dependência do SDK. As mensagens são montadas SÓ a partir do
texto da regra (e do código do provedor, quando é um identificador curto e seguro):
``message``/``details``/``hint`` brutos nunca são copiados, pois podem conter valores de
linhas ou dados do usuário (research/02 §10.3). Única leitura de ``details``: a contagem
de linhas do ``PGRST116``, e apenas o número é usado.

Decisões de desempate documentadas (a tabela do research/02 tem sobreposições):

* Código prevalece sobre status HTTP; o status só decide quando o código é desconhecido.
* ``42501`` é sempre ``PermissionDeniedError`` (o PostgREST responde 401 para o papel anon);
  um 401 sem código reconhecido é ``AuthenticationError``.
* Storage ``unauthorized`` genérico: 401 -> ``AuthenticationError``; demais -> ``PermissionDeniedError``.
* Storage "demais" (status HTTP conhecido, código desconhecido): ``UploadError``/``DownloadError``
  conforme a operação; sem status, ``UnexpectedError``.
* Extensão: 408 em tabelas é tratado como timeout (retryable).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from bai_supabase.errors.exceptions import (
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
    RecordNotFoundError,
    ReferenceViolationError,
    ServiceUnavailableError,
    SupabaseIntegrationError,
    UnexpectedError,
    UploadError,
    ValidationError,
)
from bai_supabase.errors.raw import RawError

_SAFE_CODE = re.compile(r"^[A-Za-z0-9_.:\- ]{1,64}$")
_SAFE_TYPE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]{0,80}$")
_ROWS = re.compile(r"contains\s+(\d+)\s+rows?", re.IGNORECASE)
_SQLSTATE = r"[0-9A-Z]{3}"


@dataclass(frozen=True)
class _Rule:
    """Regra de mapeamento: classe do domínio, texto fixo e ``retryable`` (None = padrão da classe)."""

    exc: type
    text: str
    retryable: Optional[bool] = None


# --------------------------------------------------------------------------- tabelas (§5.2)
_UNIQUE = _Rule(DuplicateRecordError, "violação de unicidade")
_FOREIGN_KEY = _Rule(ReferenceViolationError, "violação de chave estrangeira")
_BAD_DATA = _Rule(DataError, "o servidor rejeitou o dado enviado")
_FORBIDDEN = _Rule(PermissionDeniedError, "permissão insuficiente (RLS, privilégio ou política)")
_AUTH = _Rule(AuthenticationError, "chave ou JWT inválido ou expirado")
_MISSING_RELATION = _Rule(
    ConfigurationError, "tabela, coluna ou função inexistente (nome incorreto ou schema desatualizado)"
)
_UNAVAILABLE = _Rule(ServiceUnavailableError, "serviço indisponível")
_POOL_TIMEOUT = _Rule(OperationTimeoutError, "tempo esgotado aguardando conexão do pool")
_STATEMENT_TIMEOUT = _Rule(OperationTimeoutError, "tempo limite da instrução excedido no banco")
_RESOURCES = _Rule(ServiceUnavailableError, "recursos insuficientes no banco")
_SERIALIZATION = _Rule(ServiceUnavailableError, "conflito transitório de transação (serialização ou deadlock)")
_RATE_LIMIT = _Rule(RateLimitError, "limite de requisições excedido")
_SERVER_ERROR = _Rule(ServiceUnavailableError, "erro interno do serviço")
_GATEWAY_TIMEOUT = _Rule(OperationTimeoutError, "tempo limite excedido no servidor")
_CONFLICT = _Rule(ConflictError, "conflito de estado")

_TABLE_CODES: dict[str, _Rule] = {
    "23505": _UNIQUE,
    "23503": _FOREIGN_KEY,
    "23502": _Rule(DataError, "valor nulo em coluna obrigatória"),
    "23514": _Rule(DataError, "violação de restrição de verificação (check)"),
    "PGRST204": _Rule(DataError, "coluna inexistente na tabela"),
    "42501": _FORBIDDEN,
    "PGRST301": _AUTH,
    "PGRST302": _AUTH,
    "PGRST303": _AUTH,
    "42P01": _MISSING_RELATION,
    "PGRST205": _MISSING_RELATION,
    "PGRST202": _MISSING_RELATION,
    "PGRST000": _UNAVAILABLE,
    "PGRST001": _UNAVAILABLE,
    "PGRST002": _UNAVAILABLE,
    "PGRST003": _POOL_TIMEOUT,
    "57014": _STATEMENT_TIMEOUT,
    "40001": _SERIALIZATION,
    "40P01": _SERIALIZATION,
}

_TABLE_PREFIXES: tuple[tuple["re.Pattern[str]", _Rule], ...] = (
    (re.compile(rf"^22{_SQLSTATE}$"), _BAD_DATA),
    (re.compile(rf"^08{_SQLSTATE}$"), _UNAVAILABLE),
    (re.compile(rf"^53{_SQLSTATE}$"), _RESOURCES),
)

_TABLE_DATA_STATUS = frozenset({400, 406, 415, 416, 422})
_TABLE_STATUS: dict[int, _Rule] = {
    401: _AUTH,
    403: _FORBIDDEN,
    408: _GATEWAY_TIMEOUT,
    409: _CONFLICT,
    429: _RATE_LIMIT,
    503: _UNAVAILABLE,
    504: _GATEWAY_TIMEOUT,
}


def _single_row_rule(raw: RawError) -> _Rule:
    """``PGRST116``: 0 linhas -> não encontrado; mais de uma (ou desconhecido) -> dado inválido."""
    match = _ROWS.search(raw.details or "")
    if match and int(match.group(1)) == 0:
        return _Rule(RecordNotFoundError, "registro não encontrado")
    return _Rule(DataError, "a consulta singular retornou mais de um registro")


def _table_rule_by_status(status: Optional[int]) -> Optional[_Rule]:
    if status is None:
        return None
    if status in _TABLE_STATUS:
        return _TABLE_STATUS[status]
    if status >= 500:
        return _SERVER_ERROR
    if status in _TABLE_DATA_STATUS:
        return _BAD_DATA
    return None


def _table_rule(raw: RawError) -> Optional[_Rule]:
    code = (raw.code or "").strip().upper()
    if code == "PGRST116":
        return _single_row_rule(raw)
    if code in _TABLE_CODES:
        return _TABLE_CODES[code]
    for pattern, rule in _TABLE_PREFIXES:
        if pattern.match(code):
            return rule
    return _table_rule_by_status(raw.status)


# --------------------------------------------------------------------------- storage (§5.3)
_NOT_FOUND = _Rule(
    FileNotFoundInStorageError,
    "objeto não encontrado ou sem permissão de acesso (o Storage devolve 404 nos dois casos)",
)
_NO_BUCKET = _Rule(ConfigurationError, "bucket inexistente ou sem acesso")
_EXISTS = _Rule(FileAlreadyExistsError, "o objeto já existe")
_TOO_LARGE = _Rule(FileTooLargeError, "arquivo acima do limite de tamanho")
_INVALID = _Rule(ValidationError, "requisição de storage inválida")
_DENIED = _Rule(PermissionDeniedError, "acesso negado pelo Storage (política do bucket ou RLS)")
_STORAGE_AUTH = _Rule(AuthenticationError, "chave ou JWT inválido, expirado ou assinatura incorreta")
_INTEGRITY = _Rule(UploadError, "falha de integridade no envio (checksum ou parte ausente)", retryable=True)
_LOCKED = _Rule(ServiceUnavailableError, "recurso temporariamente bloqueado")
_STORAGE_TIMEOUT = _Rule(OperationTimeoutError, "tempo limite do banco do Storage excedido")
_SLOW_DOWN = _Rule(RateLimitError, "limite de requisições do Storage excedido")

_STORAGE_CODES: dict[str, _Rule] = {
    "nosuchkey": _NOT_FOUND,
    "notfound": _NOT_FOUND,
    "nosuchbucket": _NO_BUCKET,
    "bucketnotfound": _NO_BUCKET,
    "resourcealreadyexists": _EXISTS,
    "keyalreadyexists": _EXISTS,
    "alreadyexists": _EXISTS,
    "duplicate": _EXISTS,
    "entitytoolarge": _TOO_LARGE,
    "payloadtoolarge": _TOO_LARGE,
    "invalidmimetype": _INVALID,
    "invalidkey": _INVALID,
    "invalidbucketname": _INVALID,
    "invalidrequest": _INVALID,
    "missingparameter": _INVALID,
    "accessdenied": _DENIED,
    "invalidjwt": _STORAGE_AUTH,
    "invalidsignature": _STORAGE_AUTH,
    "signaturedoesnotmatch": _STORAGE_AUTH,
    "invalidchecksum": _INTEGRITY,
    "missingpart": _INTEGRITY,
    "resourcelocked": _LOCKED,
    "locktimeout": _LOCKED,
    "databasetimeout": _STORAGE_TIMEOUT,
    "slowdown": _SLOW_DOWN,
    "internalerror": _Rule(ServiceUnavailableError, "erro interno do Storage"),
    "databaseerror": _Rule(ServiceUnavailableError, "erro de banco no Storage"),
    "internalservererror": _Rule(ServiceUnavailableError, "erro interno do Storage"),
}

_STORAGE_STATUS: dict[int, _Rule] = {
    400: _INVALID,
    401: _STORAGE_AUTH,
    403: _DENIED,
    404: _NOT_FOUND,
    409: _EXISTS,
    413: _TOO_LARGE,
    423: _LOCKED,
    429: _SLOW_DOWN,
    503: _Rule(ServiceUnavailableError, "Storage indisponível"),
    504: _STORAGE_TIMEOUT,
    544: _STORAGE_TIMEOUT,
}


def _norm(code: Optional[str]) -> str:
    return re.sub(r"[^a-z0-9]", "", (code or "").lower())


def _storage_rule(raw: RawError, operation: str) -> Optional[_Rule]:
    code = _norm(raw.code)
    message = (raw.message or "").lower()
    if code == "notfound" and raw.status == 404 and "bucket" in message:
        return _NO_BUCKET  # o Storage legado devolve not_found também para bucket
    if code == "unauthorized":
        return _STORAGE_AUTH if raw.status == 401 else _DENIED
    op = operation.lower()
    if code == "bucketnotfound" and raw.status == 404 and any(k in op for k in ("download", "info", "signed_url")):
        # Quirk real da API: ler objeto inexistente num bucket existente devolve 404 "Bucket not found".
        return _NOT_FOUND
    if "already exists" in message and raw.status in (400, 409):
        return _EXISTS  # TUS responde 400 "Asset Already Exists" (docs: resumable uploads)
    if code in _STORAGE_CODES:
        return _STORAGE_CODES[code]
    status = raw.status
    if status is None:
        return None
    if status in _STORAGE_STATUS:
        return _STORAGE_STATUS[status]
    if status >= 500:
        return _Rule(ServiceUnavailableError, "erro interno do Storage")
    if "upload" in op:
        return _Rule(UploadError, "falha de upload no Storage")
    if "download" in op:
        return _Rule(DownloadError, "falha de download no Storage")
    return None


# --------------------------------------------------------------------------- transporte (§5.4)
_TRANSPORT: dict[str, _Rule] = {
    "timeout": _Rule(OperationTimeoutError, "tempo esgotado na conexão ou na leitura"),
    "connect": _Rule(ServiceUnavailableError, "falha de conexão, DNS ou rede"),
    "decode": _Rule(ServiceUnavailableError, "resposta não decodificável (corpo inválido ou truncado)"),
}


def _transport_rule(raw: RawError) -> Optional[_Rule]:
    return _TRANSPORT.get(raw.transport_kind or "")


# --------------------------------------------------------------------------- API pública
def _safe_code(code: Optional[str]) -> Optional[str]:
    text = (code or "").strip()
    return text if _SAFE_CODE.match(text) else None


def _unexpected_text(raw: RawError, operation: str) -> str:
    kind = raw.exception_type if raw.exception_type and _SAFE_TYPE.match(raw.exception_type) else None
    suffix = f" (tipo {kind})" if kind else ""
    return f"erro não mapeado em {operation}{suffix}"


def map_raw_error(
    raw: RawError,
    *,
    operation: str,
    resource: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> SupabaseIntegrationError:
    """Converte o erro bruto normalizado em exceção do domínio (função pura).

    ``outcome_unknown`` NÃO é decidido aqui (é do executor). O chamador deve encadear a causa
    com ``raise ... from``. Erro não mapeado vira ``UnexpectedError``.
    """
    if raw.origin == "table":
        rule = _table_rule(raw)
    elif raw.origin == "storage":
        rule = _storage_rule(raw, operation)
    else:
        rule = _transport_rule(raw)

    code = _safe_code(raw.code)
    if rule is None:
        rule = _Rule(UnexpectedError, _unexpected_text(raw, operation))
        text = rule.text
    else:
        text = f"{rule.text} (código {code})" if code else rule.text

    kwargs = dict(
        operation=operation,
        resource=resource,
        retryable=rule.retryable,
        status=raw.status,
        provider_code=code,
        correlation_id=correlation_id,
    )
    if rule.exc is RateLimitError:
        retry_after = raw.retry_after
        kwargs["retry_after"] = max(0.0, float(retry_after)) if retry_after is not None else None
    return rule.exc(text, **kwargs)
