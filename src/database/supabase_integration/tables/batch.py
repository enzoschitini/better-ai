"""Lote em chunks (research/09 §3): modos stop/continue e resultado por item.

Cada chunk é UMA requisição (atômica no Postgres). Não há atomicidade entre chunks.
Retry NÃO é feito aqui: vive no executor, por chunk e só se a operação for idempotente
(insert puro nunca repete). Isolamento do item defeituoso: bisseção do chunk, somente em
``continue`` e somente para erros que provam que o chunk foi revertido (dados/conflito),
nunca para erros transitórios nem de resultado incerto. Logs: sem valores, progresso a
cada 10%.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Sequence

from src.database.supabase_integration.contracts.logging import LoggerContract
from src.database.supabase_integration.contracts.results import BatchResult, ItemOutcome
from src.database.supabase_integration.errors.exceptions import (
    ConflictError,
    DataError,
    MappingError,
    PayloadError,
    SupabaseIntegrationError,
    ValidationError,
)

Send = Callable[[Sequence[dict]], Sequence[dict]]
Decode = Callable[[dict], Any]

_ISOLATABLE = (DataError, ConflictError, PayloadError, ValidationError)


class BatchRunner:
    """Executa um lote: divide em chunks, envia, agrega ``ItemOutcome`` com o índice original."""

    def __init__(
        self,
        logger: LoggerContract,
        *,
        isolate_failures: bool = True,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._log = logger
        self._isolate = isolate_failures
        self._clock = clock

    def run(
        self,
        *,
        table: str,
        operation: str,
        rows: Sequence[dict],
        send: Send,
        decode: Decode,
        batch_size: int,
        mode: str,
    ) -> BatchResult:
        """Envia ``rows`` em chunks de ``batch_size``. ``send`` já passa pelo executor."""
        total = len(rows)
        chunks_total = -(-total // batch_size)
        started = self._clock()
        self._log.info(
            "lote iniciado", table=table, operation=operation, total_items=total,
            batch_size=batch_size, chunks=chunks_total, mode=mode,
        )
        outcomes: list[ItemOutcome] = []
        chunks_failed = 0
        stopped = False
        last_pct = 0
        for index, start in enumerate(range(0, total, batch_size)):
            chunk = list(rows[start : start + batch_size])
            t0 = self._clock()
            try:
                returned = send(chunk)
                part = self._ok(start, chunk, returned, decode)
            except SupabaseIntegrationError as exc:
                chunks_failed += 1
                part = self._failed_chunk(mode, start, chunk, exc, send, decode)
                self._log.error(
                    "falha de chunk em lote", table=table, operation=operation, chunk=index,
                    items_from=start, items_to=start + len(chunk) - 1,
                    error_class=type(exc).__name__, status=exc.status, retryable=exc.retryable,
                    outcome_unknown=exc.outcome_unknown,
                )
            else:
                self._log.debug(
                    "chunk concluído", table=table, operation=operation, chunk=index, size=len(chunk),
                    duration_ms=round((self._clock() - t0) * 1000, 1),
                )
            outcomes.extend(part)
            if mode == "stop" and any(not o.ok for o in part):
                stopped = index < chunks_total - 1
                break
            pct = int((index + 1) / chunks_total * 10)
            if chunks_total > 1 and pct > last_pct and index + 1 < chunks_total:
                last_pct = pct
                self._log.info(
                    "progresso do lote", table=table, operation=operation, chunks_done=index + 1,
                    chunks_total=chunks_total, items_ok=sum(o.ok for o in outcomes),
                    items_failed=sum(not o.ok for o in outcomes),
                )
        result = BatchResult(items=outcomes, stopped_early=stopped)
        emit = self._log.info if result.all_ok else self._log.warning
        emit(
            "lote concluído", table=table, operation=operation, total_items=total,
            succeeded=result.succeeded, failed=result.failed, chunks_total=chunks_total,
            chunks_failed=chunks_failed, stopped_early=stopped,
            duration_ms=round((self._clock() - started) * 1000, 1),
        )
        return result

    # ------------------------------------------------------------------ chunk
    def _ok(self, start: int, chunk: Sequence[dict], returned: Sequence[dict], decode: Decode) -> list[ItemOutcome]:
        """Sucesso do chunk. Linhas devolvidas só casam com itens se vierem em número igual."""
        aligned = len(returned) == len(chunk)
        out: list[ItemOutcome] = []
        for i in range(len(chunk)):
            entity, error = None, None
            if aligned:
                try:
                    entity = decode(returned[i])
                except MappingError as exc:  # gravado no servidor, mas não decodificável
                    error = exc
            out.append(ItemOutcome(index=start + i, ok=True, entity=entity, error=error))
        return out

    def _failed_chunk(
        self, mode: str, start: int, chunk: Sequence[dict], exc: SupabaseIntegrationError, send: Send, decode: Decode
    ) -> list[ItemOutcome]:
        if self._isolate and mode == "continue" and self._isolatable(exc):
            return self._bisect(start, chunk, exc, send, decode)
        return [ItemOutcome(index=start + i, ok=False, error=exc) for i in range(len(chunk))]

    @staticmethod
    def _isolatable(exc: SupabaseIntegrationError) -> bool:
        """Só erros que provam reversão do chunk (dado/conflito); nunca transitório nem incerto."""
        return isinstance(exc, _ISOLATABLE) and not exc.retryable and not exc.outcome_unknown

    def _bisect(
        self, start: int, chunk: Sequence[dict], exc: SupabaseIntegrationError, send: Send, decode: Decode
    ) -> list[ItemOutcome]:
        """Divide ao meio até achar o(s) item(ns) defeituoso(s); o que passa é gravado."""
        if len(chunk) == 1:
            return [ItemOutcome(index=start, ok=False, error=exc)]
        mid = len(chunk) // 2
        out: list[ItemOutcome] = []
        for offset, part in ((0, chunk[:mid]), (mid, chunk[mid:])):
            try:
                out.extend(self._ok(start + offset, part, send(part), decode))
            except SupabaseIntegrationError as sub:
                if self._isolatable(sub):
                    out.extend(self._bisect(start + offset, part, sub, send, decode))
                else:
                    out.extend(ItemOutcome(index=start + offset + i, ok=False, error=sub) for i in range(len(part)))
        return out

