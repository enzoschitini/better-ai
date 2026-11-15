"""Hierarquia de exceções do domínio (spec: research/02 §3).

Nenhuma exceção do SDK (supabase, postgrest, storage3, httpx) deve alcançar o backend:
o adapter converte tudo para estas classes, preservando a causa em ``__cause__``.
"""

from __future__ import annotations

from typing import Optional


class SupabaseIntegrationError(Exception):
    """Raiz de todas as exceções da integração (nunca levantada diretamente)."""

    #: Padrão de ``retryable`` para a classe (research/02 §6).
    default_retryable: bool = False

    def __init__(
        self,
        message: str = "",
        *,
        operation: Optional[str] = None,
        resource: Optional[str] = None,
        retryable: Optional[bool] = None,
        status: Optional[int] = None,
        provider_code: Optional[str] = None,
        attempts: int = 1,
        correlation_id: Optional[str] = None,
        outcome_unknown: bool = False,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.operation = operation
        self.resource = resource
        self.retryable = self.default_retryable if retryable is None else retryable
        self.status = status
        self.provider_code = provider_code
        self.attempts = attempts
        self.correlation_id = correlation_id
        self.outcome_unknown = outcome_unknown

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> dict:
        """Resumo seguro (sem segredos) para logs."""
        return {
            "exception_class": type(self).__name__,
            "message": self.message,
            "operation": self.operation,
            "resource": self.resource,
            "retryable": self.retryable,
            "status": self.status,
            "provider_code": self.provider_code,
            "attempts": self.attempts,
            "correlation_id": self.correlation_id,
            "outcome_unknown": self.outcome_unknown,
        }


class ConfigurationError(SupabaseIntegrationError):
    """Configuração inválida ou ausente (variável, bucket ou tabela inexistente)."""


class SettingsError(ConfigurationError):
    """Falha agregada de validação de configuração: só NOMES, nunca valores."""

    def __init__(
        self,
        message: str = "",
        *,
        missing: Optional[list[str]] = None,
        invalid: Optional[list[tuple[str, str]]] = None,
        **kwargs,
    ) -> None:
        super().__init__(message, **kwargs)
        self.missing: list[str] = list(missing or [])
        self.invalid: list[tuple[str, str]] = list(invalid or [])


class ValidationError(SupabaseIntegrationError):
    """Entrada inválida detectada antes de ir à rede."""


class MappingError(SupabaseIntegrationError):
    """Falha ao (de)serializar um registro; cita tabela e campo, nunca o valor."""


class NotFoundError(SupabaseIntegrationError):
    """Recurso inexistente."""


class RecordNotFoundError(NotFoundError):
    """Registro (linha) inexistente."""


class FileNotFoundInStorageError(NotFoundError):
    """Objeto inexistente (ou sem permissão: o Storage devolve 404 nos dois casos)."""


class ConflictError(SupabaseIntegrationError):
    """Conflito de estado."""


class DuplicateRecordError(ConflictError):
    """Violação de unicidade."""


class ReferenceViolationError(ConflictError):
    """Violação de chave estrangeira."""


class FileAlreadyExistsError(ConflictError):
    """Objeto já existe e o upsert está desligado."""


class PermissionDeniedError(SupabaseIntegrationError):
    """RLS, política de bucket ou chave sem permissão."""


class AuthenticationError(SupabaseIntegrationError):
    """Chave/JWT inválido ou expirado."""


class PayloadError(SupabaseIntegrationError):
    """Payload recusado."""


class FileTooLargeError(PayloadError):
    """Limite de tamanho excedido."""


class OperationTimeoutError(SupabaseIntegrationError):
    """Timeout (evita colidir com ``TimeoutError`` builtin)."""

    default_retryable = True


class ServiceUnavailableError(SupabaseIntegrationError):
    """Rede, 5xx, serviço/pool indisponível."""

    default_retryable = True


class RateLimitError(SupabaseIntegrationError):
    """429 / SlowDown."""

    default_retryable = True

    def __init__(self, message: str = "", *, retry_after: Optional[float] = None, **kwargs) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class DataError(SupabaseIntegrationError):
    """O PostgREST/Postgres rejeitou o dado (tipo, not-null, check)."""


class UploadError(SupabaseIntegrationError):
    """Falha de upload não classificável em tipo mais específico."""


class DownloadError(SupabaseIntegrationError):
    """Falha de leitura/download não classificável em tipo mais específico."""


class UnexpectedError(SupabaseIntegrationError):
    """Qualquer exceção não mapeada (fallback). Ampliar o mapeamento ao ver esta."""
