"""Políticas puras de resiliência (research/02 §6-§9): sem relógio, sem I/O, sem SDK.

Contém as regras de decisão (o que repete, quanto espera, quantas tentativas) e o ponto de
extensão ``ExecutionPolicy`` (cadeia injetável; ex.: futuro circuit breaker, decisão A-04).
"""

from __future__ import annotations

from typing import Callable, Protocol, runtime_checkable

from bai_supabase.contracts.resilience import Operation, RetryPolicy, TimeoutPolicy
from bai_supabase.contracts.settings import ConnectionSettings
from bai_supabase.errors.exceptions import (
    OperationTimeoutError,
    RateLimitError,
    ServiceUnavailableError,
    SupabaseIntegrationError,
)

#: Consulta pesada: repetir agrava a carga (research/02 §7.3). Limita as tentativas.
HEAVY_QUERY_CODES = frozenset({"57014", "PGRST003"})


@runtime_checkable
class ExecutionPolicy(Protocol):
    """Gancho da cadeia de políticas; um circuit breaker seria uma implementação.

    ``before_attempt`` pode levantar uma exceção do domínio (ex.: circuito aberto, com
    ``retryable=False``) para impedir a tentativa; ela segue o mesmo caminho de uma falha
    da própria chamada.
    """

    def before_attempt(self, operation: Operation, attempt: int) -> None: ...

    def on_success(self, operation: Operation, attempt: int) -> None: ...

    def on_failure(self, operation: Operation, error: SupabaseIntegrationError, attempt: int) -> None: ...


def retry_policy_from_settings(settings: ConnectionSettings) -> RetryPolicy:
    """Deriva a política de retry da fatia de conexão (decisão C-4: total de tentativas)."""
    return RetryPolicy(
        max_attempts=settings.retry_max_attempts,
        base_delay=settings.retry_backoff_base_seconds,
        max_delay=settings.retry_backoff_max_seconds,
        budget_seconds=settings.retry_budget_seconds,
    )


def timeout_policy_from_settings(settings: ConnectionSettings) -> TimeoutPolicy:
    """Deriva os timeouts por categoria (informativo; aplicados no cliente HTTP, não no executor)."""
    return TimeoutPolicy(connect=settings.connect_timeout_seconds, table=settings.http_timeout_seconds)


def can_retry(operation: Operation, error: SupabaseIntegrationError) -> bool:
    """Só repete idempotente + reiniciável + erro ``retryable`` (research/02 §6 e §7.2)."""
    return bool(operation.idempotent and operation.restartable and error.retryable)


def max_attempts_for(policy: RetryPolicy, error: SupabaseIntegrationError) -> int:
    """Total de tentativas permitido para este erro (consulta pesada tem teto menor)."""
    if error.provider_code in HEAVY_QUERY_CODES:
        return max(1, min(policy.max_attempts, policy.heavy_query_max_attempts))
    return policy.max_attempts


def backoff_ceiling(policy: RetryPolicy, failed_attempt: int) -> float:
    """Teto exponencial da espera após a falha de número ``failed_attempt`` (1 = primeira)."""
    exponent = max(0, failed_attempt - 1)
    return min(policy.max_delay, policy.base_delay * (policy.multiplier**exponent))


def next_delay(
    policy: RetryPolicy,
    error: SupabaseIntegrationError,
    failed_attempt: int,
    uniform: Callable[[float, float], float],
) -> float:
    """Espera antes da próxima tentativa: full jitter, respeitando ``Retry-After`` (o maior vale)."""
    delay = uniform(0.0, backoff_ceiling(policy, failed_attempt))
    if policy.respect_retry_after and isinstance(error, RateLimitError) and error.retry_after is not None:
        delay = max(delay, error.retry_after)
    return max(0.0, delay)


def outcome_is_unknown(operation: Operation, error: SupabaseIntegrationError) -> bool:
    """Timeout/indisponibilidade em escrita não repetível: não se sabe se o servidor aplicou.

    Vale para operação não idempotente ou com fonte não reiniciável (research/02 §7.3).
    """
    risky = not operation.idempotent or not operation.restartable
    return risky and isinstance(error, (OperationTimeoutError, ServiceUnavailableError))
