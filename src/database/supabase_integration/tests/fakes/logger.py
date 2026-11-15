"""Logger que captura eventos em memória."""
from __future__ import annotations

from typing import Any


class CaptureLogger:
    def __init__(self, bound: dict | None = None, sink: list | None = None) -> None:
        self._bound = bound or {}
        self.events: list[tuple[str, str, dict]] = sink if sink is not None else []

    def _log(self, level: str, event: str, fields: dict) -> None:
        self.events.append((level, event, {**self._bound, **fields}))

    def debug(self, event: str, **fields: Any) -> None:
        self._log("DEBUG", event, fields)

    def info(self, event: str, **fields: Any) -> None:
        self._log("INFO", event, fields)

    def warning(self, event: str, **fields: Any) -> None:
        self._log("WARNING", event, fields)

    def error(self, event: str, **fields: Any) -> None:
        self._log("ERROR", event, fields)

    def bind(self, **fields: Any) -> "CaptureLogger":
        return CaptureLogger({**self._bound, **fields}, self.events)

    def levels(self) -> list[str]:
        return [e[0] for e in self.events]
