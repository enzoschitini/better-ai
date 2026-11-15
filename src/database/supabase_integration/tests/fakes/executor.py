"""Executor que só chama a função (sem retry/timeout) — para testes de unidade."""
from __future__ import annotations

from typing import Callable, TypeVar

from bai_supabase.contracts.resilience import Operation

T = TypeVar("T")


class PassThroughExecutor:
    def __init__(self) -> None:
        self.operations: list[Operation] = []

    def run(self, operation: Operation, fn: Callable[[], T]) -> T:
        self.operations.append(operation)
        return fn()
