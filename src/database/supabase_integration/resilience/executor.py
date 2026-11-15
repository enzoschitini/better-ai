"""Executor de resiliência: retry com backoff exponencial e full jitter (research/02 §7-§9).

Pontos de projeto:

* Único lugar com retry (constituição P8). ``max_attempts`` é o TOTAL de tentativas (1 = sem retry).
* Só repete se ``operation.idempotent`` E ``operation.restartable`` E a exceção é ``retryable``.
* ``budget_seconds`` é o teto de tempo total: se a próxima espera não couber no orçamento, desiste.
* LIMITAÇÃO: o executor NÃO interrompe chamadas síncronas em andamento. Os timeouts reais de rede
  são configurados nos clientes HTTP (``adapters/client.py``); aqui o orçamento só é aplicado
  ENTRE tentativas.
* Relógio (``monotonic``), ``sleep`` e ``uniform`` (aleatório) são injetáveis.
* Ao desistir levanta a ÚLTIMA exceção (mesmo objeto, ``__cause__`` preservado) com ``attempts``.
* Cada erro é registrado uma única vez (marca interna na exceção evita duplicar em execuções aninhadas).
* Logs sem segredos nem valores: só nomes, contagens, códigos e o resumo (já sanitizado) da exceção.
* ``policies`` aceita políticas extras (ex.: futuro circuit breaker) sem alterar o executor.
"""

from __future__ import annotations

import random
import time
import uuid
from typing import Callable, Optional, Sequence, TypeVar

from src.database.supabase_integration.contracts.logging import LoggerContract
from src.database.supabase_integration.contracts.resilience import Operation, RetryPolicy, TimeoutPolicy
from src.database.supabase_integration.contracts.settings import ConnectionSettings
from src.database.supabase_integration.errors.exceptions import (
    ConfigurationError,
    ConflictError,
    DataError,
    NotFoundError,
    PayloadError,
    SupabaseIntegrationError,
    UnexpectedError,
    ValidationError,
)
from src.database.supabase_integration.resilience.policies import (
    ExecutionPolicy,
    can_retry,
    max_attempts_for,
    next_delay,
    outcome_is_unknown,
    retry_policy_from_settings,
    timeout_policy_from_settings,
)

T = TypeVar("T")

_LOGGED_MARK = "_bai_logged"
#: Erros que são fluxo normal do backend: não merecem ERROR (research/02 §10.1).
_INFO_ERRORS = (NotFoundError,)
_WARNING_ERRORS = (ConflictError, ValidationError, PayloadError, DataError)


class ResilienceExecutorImpl:
    """Implementa ``contracts.resilience.ResilienceExecutor``."""

    def __init__(
        self,
        retry: RetryPolicy,
        logger: LoggerContract,
        *,
        timeouts: Optional[TimeoutPolicy] = None,
        policies: Sequence[ExecutionPolicy] = (),
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        uniform: Callable[[float, float], float] = random.uniform,
    ) -> None:
        if retry.max_attempts < 1:
            raise ConfigurationError("a política de retry exige ao menos 1 tentativa")
        self._retry = retry
        self._logger = logger
        self._policies = tuple(policies)
        self._monotonic = monotonic
        self._sleep = sleep
        self._uniform = uniform
        #: Informativo: timeouts por categoria aplicados no cliente HTTP, não aqui.
        self.timeouts = timeouts or TimeoutPolicy()

    @property
    def retry_policy(self) -> RetryPolicy:
        return self._retry

    # ------------------------------------------------------------------ execução
    def run(self, operation: Operation, fn: Callable[[], T]) -> T:
        correlation_id = operation.correlation_id or uuid.uuid4().hex[:12]
        log = self._logger.bind(
            operation=operation.name, resource=operation.resource, correlation_id=correlation_id
        )
        started = self._monotonic()
        log.debug(
            "operação iniciada",
            idempotent=operation.idempotent,
            max_attempts=self._retry.max_attempts,
            budget_seconds=self._retry.budget_seconds,
        )
        attempt = 0
        while True:
            attempt += 1
            try:
                self._before(operation, attempt)
                result = fn()
            except SupabaseIntegrationError as exc:
                error: SupabaseIntegrationError = exc
                raw_cause: Optional[BaseException] = None
            except Exception as exc:  # noqa: BLE001 - rede de segurança: só o domínio sai daqui
                error = UnexpectedError(f"falha não classificada em {operation.name}")
                raw_cause = exc
            else:
                self._after_success(operation, attempt)
                self._log_success(log, attempt, started)
                return result

            self._fill(error, operation, correlation_id)
            error.attempts = attempt
            if outcome_is_unknown(operation, error):
                error.outcome_unknown = True
            self._notify_failure(operation, error, attempt)

            delay = self._retry_delay(operation, error, attempt, started)
            if delay is None:
                self._log_giveup(log, error, attempt, started)
                if raw_cause is not None:
                    raise error from raw_cause
                raise error
            self._log_retry(log, error, attempt, delay, started)
            self._sleep(delay)

    # ------------------------------------------------------------------ decisão
    def _retry_delay(
        self, operation: Operation, error: SupabaseIntegrationError, attempt: int, started: float
    ) -> Optional[float]:
        """Espera até a próxima tentativa, ou None se deve desistir."""
        if not can_retry(operation, error):
            return None
        if attempt >= max_attempts_for(self._retry, error):
            return None
        delay = next_delay(self._retry, error, attempt, self._uniform)
        elapsed = self._monotonic() - started
        if elapsed + delay > self._retry.budget_seconds:
            return None
        return delay

    # ------------------------------------------------------------------ ganchos
    def _before(self, operation: Operation, attempt: int) -> None:
        for policy in self._policies:
            policy.before_attempt(operation, attempt)

    def _after_success(self, operation: Operation, attempt: int) -> None:
        for policy in self._policies:
            policy.on_success(operation, attempt)

    def _notify_failure(self, operation: Operation, error: SupabaseIntegrationError, attempt: int) -> None:
        for policy in self._policies:
            policy.on_failure(operation, error, attempt)

    @staticmethod
    def _fill(error: SupabaseIntegrationError, operation: Operation, correlation_id: str) -> None:
        if not error.operation:
            error.operation = operation.name
        if not error.resource:
            error.resource = operation.resource
        if not error.correlation_id:
            error.correlation_id = correlation_id

    # ------------------------------------------------------------------ logs
    def _elapsed_ms(self, started: float) -> int:
        return int((self._monotonic() - started) * 1000)

    def _log_success(self, log: LoggerContract, attempt: int, started: float) -> None:
        emit = log.info if attempt > 1 else log.debug
        emit("operação concluída", attempts=attempt, elapsed_ms=self._elapsed_ms(started))

    def _error_fields(self, error: SupabaseIntegrationError) -> dict:
        return {
            "exception_class": type(error).__name__,
            "status": error.status,
            "provider_code": error.provider_code,
            "retryable": error.retryable,
            "outcome_unknown": error.outcome_unknown,
            "cause": error.message,
        }

    def _log_retry(
        self, log: LoggerContract, error: SupabaseIntegrationError, attempt: int, delay: float, started: float
    ) -> None:
        log.warning(
            "tentativa falhou; nova tentativa agendada",
            attempt=attempt,
            max_attempts=max_attempts_for(self._retry, error),
            wait_seconds=round(delay, 3),
            elapsed_ms=self._elapsed_ms(started),
            **self._error_fields(error),
        )

    def _log_giveup(
        self, log: LoggerContract, error: SupabaseIntegrationError, attempt: int, started: float
    ) -> None:
        if getattr(error, _LOGGED_MARK, False):
            return  # já registrado por outra fronteira: cada erro uma vez
        setattr(error, _LOGGED_MARK, True)
        if isinstance(error, _INFO_ERRORS):
            emit = log.info
        elif isinstance(error, _WARNING_ERRORS):
            emit = log.warning
        else:
            emit = log.error
        emit(
            "operação falhou",
            attempts=attempt,
            elapsed_ms=self._elapsed_ms(started),
            **self._error_fields(error),
        )


def build_executor(
    settings: ConnectionSettings,
    logger: LoggerContract,
    *,
    policies: Sequence[ExecutionPolicy] = (),
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    uniform: Callable[[float, float], float] = random.uniform,
) -> ResilienceExecutorImpl:
    """Monta o executor a partir de ``ConnectionSettings`` (fatia de conexão)."""
    return ResilienceExecutorImpl(
        retry_policy_from_settings(settings),
        logger,
        timeouts=timeout_policy_from_settings(settings),
        policies=policies,
        monotonic=monotonic,
        sleep=sleep,
        uniform=uniform,
    )
