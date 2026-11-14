"""Contrato de logger injetável (constituição P7)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LoggerContract(Protocol):
    """Logger estruturado: ``event`` é uma frase curta; detalhes vão em ``fields``.

    Implementações NUNCA devem registrar segredos; ``fields`` passa por sanitizador.
    """

    def debug(self, event: str, **fields: Any) -> None: ...

    def info(self, event: str, **fields: Any) -> None: ...

    def warning(self, event: str, **fields: Any) -> None: ...

    def error(self, event: str, **fields: Any) -> None: ...

    def bind(self, **fields: Any) -> "LoggerContract":
        """Devolve um logger que acrescenta ``fields`` a todo evento (ex.: correlation_id)."""
        ...
