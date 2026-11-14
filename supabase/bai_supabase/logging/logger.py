"""Logger estruturado injetável (constituição P7; spec FR-T3; research/03 §5.4).

Níveis configuráveis, cor ANSI por nível (o nível textual SEMPRE aparece), formatos
``pretty`` (uma linha legível) e ``json`` (uma linha JSON). Tudo passa pelo sanitizador
antes de formatar. Não usa o ``logging`` da stdlib nem configura handlers globais.
"""

from __future__ import annotations

import copy
import json
import sys
import threading
from collections.abc import Callable, Iterable, Mapping
from datetime import datetime, timezone
from typing import Any, Optional, TextIO

from bai_supabase.config.sources import no_color_requested
from bai_supabase.contracts.settings import LoggingSettings
from bai_supabase.errors import ConfigurationError
from bai_supabase.logging.sanitizer import sanitize, sanitize_fields

LEVELS: Mapping[str, int] = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}
COLOR_MODES = ("auto", "on", "off")
FORMATS = ("pretty", "json")

_RESET = "\x1b[0m"
_DIM = "\x1b[2m"
_LEVEL_COLOR = {"DEBUG": "\x1b[36m", "INFO": "\x1b[32m", "WARNING": "\x1b[33m", "ERROR": "\x1b[1;31m"}
_SLOW_COLOR = "\x1b[1;33m"

#: Campos mostrados primeiro, nesta ordem, no formato pretty; ``correlation_id`` vai por último.
_FIELD_ORDER = (
    "operation", "resource", "attempt", "max_attempts", "status", "outcome",
    "count", "size_bytes", "duration_ms", "slow",
)
_LAST_FIELDS = ("correlation_id",)
_RESERVED_JSON = frozenset({"ts", "level", "event"})


def _validate(settings: LoggingSettings) -> tuple[str, str, str]:
    level, color, fmt = settings.level.upper(), settings.color.lower(), settings.format.lower()
    if level not in LEVELS:
        raise ConfigurationError("nível de log inválido: use DEBUG, INFO, WARNING ou ERROR")
    if color not in COLOR_MODES:
        raise ConfigurationError("cor de log inválida: use auto, on ou off")
    if fmt not in FORMATS:
        raise ConfigurationError("formato de log inválido: use pretty ou json")
    return level, color, fmt


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StructuredLogger:
    """Implementa ``LoggerContract`` (``bai_supabase.contracts.logging``). Imutável após criada; ``bind`` devolve uma cópia."""

    def __init__(
        self,
        settings: LoggingSettings,
        *,
        stream: Optional[TextIO] = None,
        clock: Optional[Callable[[], datetime]] = None,
        no_color: Optional[bool] = None,
        extra_secrets: Iterable[Any] = (),
        bound: Optional[Mapping[str, Any]] = None,
    ) -> None:
        level, color, fmt = _validate(settings)
        self._threshold = LEVELS[level]
        self._color = color
        self._format = fmt
        self._slow_ms = settings.slow_ms
        self._max_chars = settings.max_field_chars
        self._stream = stream
        self._clock = clock or _utc_now
        self._no_color = no_color_requested() if no_color is None else no_color
        self._extra_secrets = tuple(extra_secrets)
        self._bound: dict[str, Any] = dict(bound or {})
        self._lock = threading.Lock()

    # --- contrato -----------------------------------------------------------------
    def debug(self, event: str, /, **fields: Any) -> None:
        self.log("DEBUG", event, **fields)

    def info(self, event: str, /, **fields: Any) -> None:
        self.log("INFO", event, **fields)

    def warning(self, event: str, /, **fields: Any) -> None:
        self.log("WARNING", event, **fields)

    def error(self, event: str, /, **fields: Any) -> None:
        self.log("ERROR", event, **fields)

    def bind(self, **fields: Any) -> "StructuredLogger":
        child = copy.copy(self)  # compartilha stream, relógio e trava
        child._bound = {**self._bound, **fields}
        return child

    # --- núcleo -------------------------------------------------------------------
    def is_enabled(self, level: str) -> bool:
        return LEVELS[level.upper()] >= self._threshold

    def log(self, level: str, event: str, /, **fields: Any) -> None:
        """Registra ``event``; nunca levanta exceção por falha de saída."""
        level = level.upper()
        merged = {**self._bound, **fields}
        level = self._escalate_if_slow(level, merged)
        if LEVELS[level] < self._threshold:
            return
        clean = sanitize_fields(merged, max_chars=self._max_chars, extra_secrets=self._extra_secrets)
        text = sanitize(str(event), max_chars=self._max_chars * 2, extra_secrets=self._extra_secrets)
        stamp = self._clock()
        out = self._stream if self._stream is not None else sys.stderr
        line = (
            self._render_json(stamp, level, text, clean)
            if self._format == "json"
            else self._render_pretty(stamp, level, text, clean, self._use_color(out))
        )
        try:
            with self._lock:
                out.write(line + "\n")
                flush = getattr(out, "flush", None)
                if flush is not None:
                    flush()
        except Exception:  # log nunca derruba a operação
            pass

    # --- internos -----------------------------------------------------------------
    def _escalate_if_slow(self, level: str, fields: dict[str, Any]) -> str:
        """Operação lenta ganha ``slow=true`` e sobe para WARNING (se ainda abaixo)."""
        duration = fields.get("duration_ms")
        is_number = isinstance(duration, (int, float)) and not isinstance(duration, bool)
        if self._slow_ms > 0 and is_number and duration > self._slow_ms:
            fields["slow"] = True
            return level if LEVELS[level] >= LEVELS["WARNING"] else "WARNING"
        return level

    def _use_color(self, out: TextIO) -> bool:
        if self._color == "on":
            return True
        if self._color == "off" or self._no_color:
            return False
        try:
            return bool(out.isatty())
        except Exception:
            return False

    def _render_json(self, stamp: datetime, level: str, event: str, fields: dict[str, Any]) -> str:
        record: dict[str, Any] = {"ts": stamp.isoformat(), "level": level, "event": event}
        for key, value in fields.items():
            record[f"field_{key}" if key in _RESERVED_JSON else key] = value
        return json.dumps(record, ensure_ascii=False, separators=(",", ":"), default=str, allow_nan=False)

    def _render_pretty(self, stamp: datetime, level: str, event: str, fields: dict[str, Any], color: bool) -> str:
        clock = stamp.strftime("%H:%M:%S.") + f"{stamp.microsecond // 1000:03d}"
        label = f"{level:<7}"
        if color:
            label = f"{_LEVEL_COLOR[level]}{label}{_RESET}"
            clock = f"{_DIM}{clock}{_RESET}"
        parts = [clock, label, " ".join(event.split()) or "-"]
        for key in self._ordered(fields):
            parts.append(_pair(key, fields[key], color))
        return " ".join(parts)

    @staticmethod
    def _ordered(fields: dict[str, Any]) -> list[str]:
        first = [k for k in _FIELD_ORDER if k in fields]
        last = [k for k in _LAST_FIELDS if k in fields]
        middle = sorted(k for k in fields if k not in first and k not in last)
        return first + middle + last

    def __repr__(self) -> str:
        return f"StructuredLogger(format={self._format!r}, bound={sorted(self._bound)})"


def _scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        if value and all(c.isprintable() and not c.isspace() and c not in "\"'=" for c in value):
            return value
        return json.dumps(value, ensure_ascii=False)
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)


def _pair(key: str, value: Any, color: bool) -> str:
    name = f"{_DIM}{key}{_RESET}" if color else key
    text = _scalar(value)
    if color and key == "slow":
        text = f"{_SLOW_COLOR}{text}{_RESET}"
    return f"{name}={text}"


def build_logger(
    settings: LoggingSettings,
    stream: Optional[TextIO] = None,
    *,
    clock: Optional[Callable[[], datetime]] = None,
    no_color: Optional[bool] = None,
    extra_secrets: Iterable[Any] = (),
) -> StructuredLogger:
    """Factory: cria o logger a partir da fatia ``LoggingSettings`` (stream padrão: stderr)."""
    return StructuredLogger(settings, stream=stream, clock=clock, no_color=no_color, extra_secrets=extra_secrets)
