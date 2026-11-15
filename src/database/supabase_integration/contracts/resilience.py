"""Contrato do executor de resiliência (research/02 §7-§9)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Literal, Optional, Protocol, TypeVar, runtime_checkable

T = TypeVar("T")

Category = Literal["table", "batch", "file_transfer", "file_meta"]


@dataclass(frozen=True)
class Operation:
    """Descreve a operação para o executor decidir timeout e retry."""

    name: str  # ex.: "table.insert", "storage.upload"
    resource: Optional[str] = None  # tabela ou bucket[/path]
    #: Repetir é seguro? (research/02 §7.2). Só se repete idempotente + retryable.
    idempotent: bool = False
    category: Category = "table"
    #: Se a fonte de dados não pode ser relida do início, não repetir.
    restartable: bool = True
    correlation_id: Optional[str] = None


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3  # total; 1 = sem retry
    base_delay: float = 0.5
    multiplier: float = 2.0
    max_delay: float = 8.0
    budget_seconds: float = 30.0
    respect_retry_after: bool = True
    #: Limite de retries para statement timeout / pool timeout (research/02 §7.3).
    heavy_query_max_attempts: int = 2


@dataclass(frozen=True)
class TimeoutPolicy:
    connect: float = 3.0
    table: float = 10.0
    batch: float = 60.0
    file_meta: float = 10.0
    file_transfer: float = 120.0
    #: Overrides por categoria (sobrescrevem os campos acima).
    overrides: dict = field(default_factory=dict)


@runtime_checkable
class ResilienceExecutor(Protocol):
    """Aplica timeout/retry em volta de uma chamada de adapter.

    ``fn`` já levanta exceções DO DOMÍNIO (o adapter mapeia). O executor repete só se
    ``operation.idempotent`` e a exceção for ``retryable``; ao desistir levanta a última
    exceção com ``attempts`` preenchido e ``__cause__`` preservado.
    """

    def run(self, operation: Operation, fn: Callable[[], T]) -> T: ...
