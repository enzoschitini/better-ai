"""Executor de resiliência com relógio, sleep e aleatório falsos (research/02 §7, §13)."""
from __future__ import annotations

import pytest

from bai_supabase.contracts.resilience import Operation, ResilienceExecutor, RetryPolicy
from bai_supabase.contracts.secret import Secret
from bai_supabase.contracts.settings import ConnectionSettings
from bai_supabase.errors import (
    AuthenticationError,
    ConfigurationError,
    DuplicateRecordError,
    OperationTimeoutError,
    RateLimitError,
    RecordNotFoundError,
    ServiceUnavailableError,
    UnexpectedError,
)
from bai_supabase.resilience import ResilienceExecutorImpl, build_executor
from bai_supabase.resilience.policies import backoff_ceiling
from tests.fakes.logger import CaptureLogger

SECRET = "SEGREDO-PLANTADO-123"


class FakeClock:
    """Relógio determinístico: ``sleep`` avança o tempo; ``uniform`` devolve a fração do teto."""

    def __init__(self, fraction: float = 1.0) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []
        self.fraction = fraction
        self.ranges: list[tuple[float, float]] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds

    def uniform(self, a: float, b: float) -> float:
        self.ranges.append((a, b))
        return a + (b - a) * self.fraction


def make(policy: RetryPolicy | None = None, clock: FakeClock | None = None, **kw):
    clock = clock or FakeClock()
    logger = CaptureLogger()
    executor = ResilienceExecutorImpl(
        policy or RetryPolicy(),
        logger,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
        uniform=clock.uniform,
        **kw,
    )
    return executor, clock, logger


class Flaky:
    """Falha com as exceções dadas (na ordem) e depois devolve ``result``."""

    def __init__(self, errors, result="ok"):
        self.errors = list(errors)
        self.result = result
        self.calls = 0

    def __call__(self):
        self.calls += 1
        if self.errors:
            raise self.errors.pop(0)
        return self.result


READ = Operation("table.select", resource="t", idempotent=True)
INSERT = Operation("table.insert", resource="t", idempotent=False)
UPSERT = Operation("table.upsert", resource="t", idempotent=True)
BATCH = Operation("table.insert_many", resource="t", idempotent=False, category="batch")


def unavailable() -> ServiceUnavailableError:
    return ServiceUnavailableError("indisponível", provider_code="PGRST002", status=503)


def test_conforms_to_contract():
    executor, _, _ = make()
    assert isinstance(executor, ResilienceExecutor)


def test_success_first_try_no_sleep_and_debug_logs_only():
    executor, clock, logger = make()
    assert executor.run(READ, Flaky([])) == "ok"
    assert clock.sleeps == [] and set(logger.levels()) == {"DEBUG"}


def test_retries_until_success_and_logs_each_retry_once():
    executor, clock, logger = make(RetryPolicy(max_attempts=3, base_delay=0.5, multiplier=2, max_delay=8))
    fn = Flaky([unavailable(), unavailable()])
    assert executor.run(READ, fn) == "ok"
    assert fn.calls == 3
    assert clock.sleeps == [0.5, 1.0]  # fração 1.0 do teto exponencial (0,5 e 1,0)
    assert logger.levels().count("WARNING") == 2 and "ERROR" not in logger.levels()
    warnings = [e for e in logger.events if e[0] == "WARNING"]
    assert [w[2]["attempt"] for w in warnings] == [1, 2]
    assert [w[2]["wait_seconds"] for w in warnings] == [0.5, 1.0]
    assert warnings[0][2]["exception_class"] == "ServiceUnavailableError"
    done = [e for e in logger.events if e[1] == "operação concluída"][0]
    assert done[0] == "INFO" and done[2]["attempts"] == 3


def test_full_jitter_draws_between_zero_and_ceiling():
    executor, clock, _ = make(RetryPolicy(max_attempts=4, base_delay=1, multiplier=2, max_delay=3), FakeClock(0.5))
    with pytest.raises(ServiceUnavailableError):
        executor.run(READ, Flaky([unavailable()] * 4))
    assert clock.ranges == [(0.0, 1.0), (0.0, 2.0), (0.0, 3.0)]  # teto de espera = max_delay
    assert clock.sleeps == [0.5, 1.0, 1.5]


def test_backoff_ceiling_formula():
    p = RetryPolicy(base_delay=0.5, multiplier=2, max_delay=8)
    assert [backoff_ceiling(p, n) for n in (1, 2, 3, 4, 5, 6)] == [0.5, 1.0, 2.0, 4.0, 8.0, 8.0]


def test_gives_up_after_max_attempts_raising_same_object_with_attempts():
    executor, _, logger = make(RetryPolicy(max_attempts=3))
    cause = RuntimeError("sdk")
    error = OperationTimeoutError("timeout")
    error.__cause__ = cause
    fn = Flaky([error, error, error])
    with pytest.raises(OperationTimeoutError) as info:
        executor.run(READ, fn)
    assert info.value is error and info.value.__cause__ is cause
    assert error.attempts == 3 and error.retryable is True
    assert fn.calls == 3
    assert logger.levels().count("ERROR") == 1 and logger.levels().count("WARNING") == 2
    assert error.operation == "table.select" and error.resource == "t" and error.correlation_id


def test_max_attempts_one_means_no_retry():
    executor, clock, _ = make(RetryPolicy(max_attempts=1))
    fn = Flaky([unavailable()])
    with pytest.raises(ServiceUnavailableError):
        executor.run(READ, fn)
    assert fn.calls == 1 and clock.sleeps == []


def test_budget_caps_total_time():
    policy = RetryPolicy(max_attempts=10, base_delay=2, multiplier=2, max_delay=100, budget_seconds=5)
    executor, clock, _ = make(policy)  # esperas: 2 (t=2), 4 (t=6 > 5 -> desiste)
    fn = Flaky([unavailable()] * 10)
    with pytest.raises(ServiceUnavailableError) as info:
        executor.run(READ, fn)
    assert clock.sleeps == [2.0] and fn.calls == 2 and info.value.attempts == 2
    assert clock.now <= policy.budget_seconds


def test_budget_counts_time_spent_inside_calls():
    clock = FakeClock()
    executor, _, _ = make(RetryPolicy(max_attempts=5, base_delay=1, budget_seconds=10), clock)

    def slow_failure():
        clock.now += 9.5
        raise unavailable()

    with pytest.raises(ServiceUnavailableError) as info:
        executor.run(READ, slow_failure)
    assert info.value.attempts == 1 and clock.sleeps == []


def test_retry_after_wins_when_larger_than_backoff():
    executor, clock, _ = make(RetryPolicy(max_attempts=2, base_delay=0.5, budget_seconds=60))
    limited = RateLimitError("429", retry_after=10.0, status=429)
    assert executor.run(READ, Flaky([limited])) == "ok"
    assert clock.sleeps == [10.0]


def test_backoff_wins_when_larger_than_retry_after():
    executor, clock, _ = make(RetryPolicy(max_attempts=2, base_delay=4, max_delay=8))
    assert executor.run(READ, Flaky([RateLimitError("429", retry_after=1.0)])) == "ok"
    assert clock.sleeps == [4.0]


def test_retry_after_beyond_budget_gives_up_without_sleeping():
    executor, clock, _ = make(RetryPolicy(max_attempts=3, budget_seconds=5))
    with pytest.raises(RateLimitError):
        executor.run(READ, Flaky([RateLimitError("429", retry_after=30.0)]))
    assert clock.sleeps == []


def test_retry_after_ignored_when_policy_disables_it():
    executor, clock, _ = make(RetryPolicy(max_attempts=2, base_delay=1, respect_retry_after=False))
    executor.run(READ, Flaky([RateLimitError("429", retry_after=30.0)]))
    assert clock.sleeps == [1.0]


# ---------------------------------------------------------------- idempotência
@pytest.mark.parametrize("operation", [INSERT, BATCH])
def test_non_idempotent_operations_never_retry(operation):
    executor, clock, _ = make()
    fn = Flaky([unavailable()])
    with pytest.raises(ServiceUnavailableError):
        executor.run(operation, fn)
    assert fn.calls == 1 and clock.sleeps == []


def test_upsert_retries():
    executor, _, _ = make()
    fn = Flaky([unavailable()])
    assert executor.run(UPSERT, fn) == "ok" and fn.calls == 2


def test_non_restartable_source_is_not_retried():
    executor, _, _ = make()
    op = Operation("storage.upload", idempotent=True, restartable=False)
    fn = Flaky([unavailable()])
    with pytest.raises(ServiceUnavailableError) as info:
        executor.run(op, fn)
    assert fn.calls == 1 and info.value.outcome_unknown is True


@pytest.mark.parametrize(
    "error", [DuplicateRecordError("x"), RecordNotFoundError("x"), AuthenticationError("x"), UnexpectedError("x")]
)
def test_non_retryable_errors_do_not_retry_even_if_idempotent(error):
    executor, clock, _ = make()
    fn = Flaky([error])
    with pytest.raises(type(error)) as info:
        executor.run(READ, fn)
    assert info.value is error and fn.calls == 1 and clock.sleeps == [] and error.attempts == 1


# ---------------------------------------------------------------- outcome_unknown
@pytest.mark.parametrize("error", [OperationTimeoutError("t"), ServiceUnavailableError("s")])
def test_outcome_unknown_on_non_idempotent_timeout_or_unavailable(error):
    executor, _, logger = make()
    with pytest.raises(type(error)) as info:
        executor.run(INSERT, Flaky([error]))
    assert info.value.outcome_unknown is True
    err_log = [e for e in logger.events if e[0] == "ERROR"]
    assert len(err_log) == 1 and err_log[0][2]["outcome_unknown"] is True


def test_outcome_not_unknown_for_other_errors_or_idempotent_ops():
    executor, _, _ = make()
    with pytest.raises(DuplicateRecordError) as dup:
        executor.run(INSERT, Flaky([DuplicateRecordError("x")]))
    assert dup.value.outcome_unknown is False
    with pytest.raises(RateLimitError) as limited:
        executor.run(INSERT, Flaky([RateLimitError("429")]))
    assert limited.value.outcome_unknown is False
    with pytest.raises(OperationTimeoutError) as timeout:
        executor.run(READ, Flaky([OperationTimeoutError("t")] * 3))
    assert timeout.value.outcome_unknown is False


# ---------------------------------------------------------------- consulta pesada
@pytest.mark.parametrize("code", ["57014", "PGRST003"])
def test_heavy_query_codes_limit_attempts(code):
    executor, clock, logger = make(RetryPolicy(max_attempts=5, heavy_query_max_attempts=2))
    errors = [OperationTimeoutError("t", provider_code=code) for _ in range(5)]
    fn = Flaky(errors)
    with pytest.raises(OperationTimeoutError) as info:
        executor.run(READ, fn)
    assert fn.calls == 2 and info.value.attempts == 2 and len(clock.sleeps) == 1
    assert logger.levels().count("WARNING") == 1


# ---------------------------------------------------------------- logs
def test_each_error_logged_once_even_through_nested_executors():
    outer, _, outer_log = make()
    inner_logger = CaptureLogger()
    inner = ResilienceExecutorImpl(RetryPolicy(max_attempts=1), inner_logger)
    error = ConfigurationError("sem tabela")
    with pytest.raises(ConfigurationError):
        outer.run(READ, lambda: inner.run(READ, Flaky([error])))
    assert inner_logger.levels().count("ERROR") == 1
    assert "ERROR" not in outer_log.levels()  # a marca evita o segundo registro


@pytest.mark.parametrize(
    "error, level",
    [
        (RecordNotFoundError("x"), "INFO"),
        (DuplicateRecordError("x"), "WARNING"),
        (AuthenticationError("x"), "ERROR"),
        (UnexpectedError("x"), "ERROR"),
    ],
)
def test_final_failure_level_by_class(error, level):
    executor, _, logger = make()
    with pytest.raises(type(error)):
        executor.run(READ, Flaky([error]))
    final = [e for e in logger.events if e[1] == "operação falhou"]
    assert len(final) == 1 and final[0][0] == level


def test_logs_carry_structured_fields_and_no_secret():
    executor, _, logger = make(RetryPolicy(max_attempts=2))
    op = Operation("table.select", resource="usuarios", idempotent=True, correlation_id="corr-1")
    error = ServiceUnavailableError("indisponível", provider_code="PGRST002", status=503)
    error.__cause__ = RuntimeError(f"detalhe com {SECRET}")
    with pytest.raises(ServiceUnavailableError):
        executor.run(op, Flaky([error, error]))
    assert all(SECRET not in repr(e) for e in logger.events)
    final = [e for e in logger.events if e[1] == "operação falhou"][0][2]
    for key in ("operation", "resource", "correlation_id", "attempts", "elapsed_ms", "status",
                "provider_code", "exception_class", "retryable", "outcome_unknown"):
        assert key in final
    assert final["correlation_id"] == "corr-1" and final["operation"] == "table.select"


def test_existing_error_fields_are_not_overwritten():
    executor, _, _ = make(RetryPolicy(max_attempts=1))
    error = ServiceUnavailableError("x", operation="outra", resource="r", correlation_id="c")
    with pytest.raises(ServiceUnavailableError):
        executor.run(READ, Flaky([error]))
    assert (error.operation, error.resource, error.correlation_id) == ("outra", "r", "c")


def test_non_domain_exception_is_wrapped_as_unexpected_with_cause():
    executor, _, logger = make()
    boom = KeyError("x")
    with pytest.raises(UnexpectedError) as info:
        executor.run(READ, Flaky([boom]))
    assert info.value.__cause__ is boom and info.value.attempts == 1
    assert logger.levels().count("ERROR") == 1


# ---------------------------------------------------------------- extensão e fábrica
class RecordingPolicy:
    def __init__(self, block_after: int | None = None):
        self.events: list = []
        self.block_after = block_after

    def before_attempt(self, operation, attempt):
        self.events.append(("before", attempt))
        if self.block_after is not None and attempt > self.block_after:
            raise ServiceUnavailableError("circuito aberto", retryable=False)

    def on_success(self, operation, attempt):
        self.events.append(("success", attempt))

    def on_failure(self, operation, error, attempt):
        self.events.append(("failure", attempt))


def test_extra_policies_are_notified():
    policy = RecordingPolicy()
    executor, _, _ = make(policies=[policy])
    executor.run(READ, Flaky([unavailable()]))
    assert policy.events == [("before", 1), ("failure", 1), ("before", 2), ("success", 2)]


def test_policy_can_block_attempts_like_a_circuit_breaker():
    policy = RecordingPolicy(block_after=1)
    executor, _, _ = make(RetryPolicy(max_attempts=5), policies=[policy])
    fn = Flaky([unavailable()] * 5)
    with pytest.raises(ServiceUnavailableError) as info:
        executor.run(READ, fn)
    assert fn.calls == 1 and info.value.retryable is False and info.value.attempts == 2


def test_invalid_policy_is_rejected():
    with pytest.raises(ConfigurationError):
        ResilienceExecutorImpl(RetryPolicy(max_attempts=0), CaptureLogger())


def test_build_executor_uses_connection_settings():
    settings = ConnectionSettings(
        url="https://x.supabase.co",
        secret_key=Secret(SECRET),
        retry_max_attempts=2,
        retry_backoff_base_seconds=0.1,
        retry_backoff_max_seconds=0.2,
        retry_budget_seconds=3,
        http_timeout_seconds=9,
    )
    clock = FakeClock()
    executor = build_executor(settings, CaptureLogger(), monotonic=clock.monotonic, sleep=clock.sleep, uniform=clock.uniform)
    retry = executor.retry_policy
    assert (retry.max_attempts, retry.base_delay, retry.max_delay, retry.budget_seconds) == (2, 0.1, 0.2, 3)
    assert executor.timeouts.table == 9
    fn = Flaky([unavailable(), unavailable()])
    with pytest.raises(ServiceUnavailableError):
        executor.run(READ, fn)
    assert fn.calls == 2
