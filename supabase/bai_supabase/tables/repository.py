"""Repositório genérico por descritor sobre ``TableTransport`` (research/06 §3, A-01).

Dependências injetadas: transporte, executor de resiliência, logger e ``TablesSettings``.
Cada método declara ao executor se é idempotente (research/02 §7.2); o retry vive só no
executor. Semântica A-01: ``get_by_id``/``update`` inexistente -> ``RecordNotFoundError``;
``find`` vazio -> lista vazia; ``delete`` inexistente -> ``removed_count=0``; lote vazio ->
``ValidationError``. Logs: operação, tabela, duração e contagem; nunca valores.
O erro que vem do executor NÃO é registrado de novo aqui.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Iterator, Optional, Sequence, TypeVar

from bai_supabase.contracts.logging import LoggerContract
from bai_supabase.contracts.query import Condition, Filter, Op, Page, PageRequest, Query
from bai_supabase.contracts.resilience import Category, Operation, ResilienceExecutor
from bai_supabase.contracts.results import BatchResult, DeleteResult
from bai_supabase.contracts.settings import TablesSettings
from bai_supabase.contracts.tables import BatchOptions, TableDescriptor
from bai_supabase.contracts.transports import SelectRequest, SelectResponse, TableTransport
from bai_supabase.errors.exceptions import RecordNotFoundError, UnexpectedError, ValidationError
from bai_supabase.tables.batch import BatchRunner
from bai_supabase.tables.pagination import Paginator
from bai_supabase.tables.serialization import EntityCodec
from bai_supabase.tables.validation import TableValidator, validate_descriptor

T = TypeVar("T")


class PostgresTableRepository:
    """Implementa ``TableRepository`` para UMA tabela, descrita por um ``TableDescriptor``."""

    def __init__(
        self,
        descriptor: TableDescriptor,
        transport: TableTransport,
        executor: ResilienceExecutor,
        logger: LoggerContract,
        settings: TablesSettings,
        *,
        isolate_failures: bool = True,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        validate_descriptor(descriptor, settings.allowlist)
        self.descriptor = descriptor
        self._transport = transport
        self._executor = executor
        self._settings = settings
        self._clock = clock
        self._log = logger.bind(component="tables", table=descriptor.name)
        self._codec = EntityCodec(descriptor)
        self._validator = TableValidator(descriptor, settings)
        self._paginator = Paginator(descriptor, settings, self._log)
        self._batch = BatchRunner(self._log, isolate_failures=isolate_failures, clock=clock)

    # ------------------------------------------------------------------ infraestrutura
    def _run(self, name: str, fn: Callable[[], T], *, idempotent: bool, category: Category = "table") -> T:
        """Executa ``fn`` pelo executor declarando a idempotência da operação."""
        op = Operation(name=f"table.{name}", resource=self.descriptor.name, idempotent=idempotent, category=category)
        return self._executor.run(op, fn)

    def _done(self, name: str, started: float, count: int, *, write: bool = False) -> None:
        emit = self._log.info if write else self._log.debug
        emit("operação de tabela concluída", operation=name, count=count, duration_ms=round((self._clock() - started) * 1000, 1))

    def _fetcher(self, name: str) -> Callable[[SelectRequest], SelectResponse]:
        """Leitura paginada pelo executor (idempotente)."""
        return lambda req: self._run(name, lambda: self._transport.select(req), idempotent=True)

    def _pk_filter(self, record_id: Any) -> Condition:
        return Condition(self.descriptor.primary_key, Op.EQ, self._validator.record_id(record_id))

    def _write_row(self, entity: Any, conflict: Sequence[str] = ()) -> dict:
        mapping = self._codec.to_mapping(entity)
        self._validator.write_columns(mapping.keys())
        return self._codec.encode_insert(mapping, allowed_managed=conflict)

    def _decode_one(self, rows: Sequence[dict], operation: str) -> Any:
        if len(rows) < 1:
            raise UnexpectedError("o servidor não devolveu o registro gravado", operation=f"table.{operation}", resource=self.descriptor.name)
        return self._codec.decode(rows[0])

    # ------------------------------------------------------------------ leitura
    def get_by_id(self, id: Any) -> Any:
        started = self._clock()
        flt = self._pk_filter(id)
        req = SelectRequest(
            table=self.descriptor.name, schema=self.descriptor.schema,
            columns=self._validator.select_columns(None), filter=flt, limit=1,
        )
        resp = self._run("get_by_id", lambda: self._transport.select(req), idempotent=True)
        if not resp.rows:
            self._log.debug("registro não encontrado", operation="get_by_id")
            raise RecordNotFoundError("registro não encontrado", operation="table.get_by_id", resource=self.descriptor.name)
        entity = self._codec.decode(resp.rows[0])
        self._done("get_by_id", started, 1)
        return entity

    def find(self, query: Optional[Query] = None) -> list:
        """Todas as linhas que casam (varre as páginas; nunca trunca no limite do servidor).

        Carrega tudo em memória: para tabelas grandes prefira ``iterate``/``list``.
        """
        started = self._clock()
        q = self._validator.query(query)
        entities = [
            self._codec.decode(row)
            for rows in self._paginator.scan(self._fetcher("find"), q)
            for row in rows
        ]
        self._done("find", started, len(entities))
        return entities

    def list(self, query: Optional[Query] = None, page: Optional[PageRequest] = None) -> Page:
        started = self._clock()
        q = self._validator.query(query)
        result = self._paginator.list_page(self._fetcher("list"), q, page or PageRequest())
        items = [self._codec.decode(row) for row in result.items]
        self._done("list", started, len(items))
        return Page(
            items=items, limit=result.limit, offset=result.offset, next_cursor=result.next_cursor,
            total=result.total, has_more=result.has_more,
        )

    def iterate(
        self, query: Optional[Query] = None, page_size: Optional[int] = None, start_after: Optional[str] = None
    ) -> Iterator[Any]:
        """Varredura preguiçosa: uma página em memória por vez. Em falha, a exceção traz ``resume_cursor``.

        A consulta é validada já na chamada (antes da primeira leitura).
        """
        q = self._validator.query(query)
        size = self._paginator.page_size(page_size)  # valida/reduz o tamanho antes de iniciar
        return self._iterate(q, size, start_after)

    def _iterate(self, q: Query, page_size: Optional[int], start_after: Optional[str]) -> Iterator[Any]:
        started = self._clock()
        pages = items = 0
        for rows in self._paginator.scan(self._fetcher("iterate"), q, page_size, start_after):
            pages += 1
            for row in rows:
                items += 1
                yield self._codec.decode(row)
        self._log.info(
            "varredura concluída", operation="iterate", pages=pages, count=items,
            duration_ms=round((self._clock() - started) * 1000, 1),
        )

    # ------------------------------------------------------------------ escrita unitária
    def insert(self, entity: Any) -> Any:
        """Não idempotente: o executor nunca repete."""
        started = self._clock()
        row = self._write_row(entity)
        d = self.descriptor
        rows = self._run("insert", lambda: self._transport.insert(d.name, d.schema, [row]), idempotent=False)
        result = self._decode_one(rows, "insert")
        self._done("insert", started, 1, write=True)
        return result

    def update(self, id: Any, changes: dict) -> Any:
        started = self._clock()
        flt = self._pk_filter(id)
        patch = self._patch(changes)
        d = self.descriptor
        rows = self._run("update", lambda: self._transport.update(d.name, d.schema, patch, flt), idempotent=True)
        if not rows:
            raise RecordNotFoundError("registro não encontrado", operation="table.update", resource=d.name)
        result = self._codec.decode(rows[0])
        self._done("update", started, 1, write=True)
        return result

    def update_where(self, filter: Filter, changes: dict) -> int:
        started = self._clock()
        flt = self._validator.non_empty_filter(filter, "update_where")
        patch = self._patch(changes)
        d = self.descriptor
        rows = self._run(
            "update_where", lambda: self._transport.update(d.name, d.schema, patch, flt),
            idempotent=True, category="batch",
        )
        self._done("update_where", started, len(rows), write=True)
        return len(rows)

    def _patch(self, changes: Any) -> dict:
        mapping = self._codec.to_changes_mapping(changes)
        if not mapping:
            raise ValidationError("alterações vazias", resource=self.descriptor.name)
        self._validator.write_columns(mapping.keys())
        return self._codec.encode_changes(mapping)

    def upsert(self, entity: Any, on_conflict: Optional[str] = None) -> Any:
        started = self._clock()
        conflict = self._validator.conflict_columns(on_conflict)
        row = self._write_row(entity, conflict)
        d = self.descriptor
        rows = self._run(
            "upsert", lambda: self._transport.upsert(d.name, d.schema, [row], on_conflict), idempotent=True
        )
        result = self._decode_one(rows, "upsert")
        self._done("upsert", started, 1, write=True)
        return result

    def delete(self, id: Any) -> DeleteResult:
        """Idempotente: inexistente = sucesso com ``removed_count=0``."""
        started = self._clock()
        flt = self._pk_filter(id)
        d = self.descriptor
        rows = self._run("delete", lambda: self._transport.delete(d.name, d.schema, flt), idempotent=True)
        self._done("delete", started, len(rows), write=True)
        return DeleteResult(removed_count=len(rows))

    def delete_where(self, filter: Filter) -> DeleteResult:
        started = self._clock()
        flt = self._validator.non_empty_filter(filter, "delete_where")
        d = self.descriptor
        rows = self._run(
            "delete_where", lambda: self._transport.delete(d.name, d.schema, flt),
            idempotent=True, category="batch",
        )
        self._done("delete_where", started, len(rows), write=True)
        return DeleteResult(removed_count=len(rows))

    # ------------------------------------------------------------------ lotes
    def insert_many(self, entities: Sequence[Any], options: Optional[BatchOptions] = None) -> BatchResult:
        """Insert em chunks. Insert puro NÃO é idempotente: sem retry; falha incerta fica marcada."""
        d = self.descriptor
        items = self._validator.non_empty_batch(entities, "insert_many")
        size, mode = self._validator.batch_options(options)
        rows = [self._write_row(e) for e in items]  # valida tudo antes de ir à rede
        return self._batch.run(
            table=d.name, operation="insert_many", rows=rows, decode=self._codec.decode,
            send=lambda chunk: self._run(
                "insert_many", lambda: self._transport.insert(d.name, d.schema, chunk),
                idempotent=False, category="batch",
            ),
            batch_size=size, mode=mode,
        )

    def upsert_many(
        self, entities: Sequence[Any], on_conflict: Optional[str] = None, options: Optional[BatchOptions] = None
    ) -> BatchResult:
        """Upsert em chunks: idempotente, portanto o executor pode repetir cada chunk."""
        d = self.descriptor
        items = self._validator.non_empty_batch(entities, "upsert_many")
        size, mode = self._validator.batch_options(options)
        conflict = self._validator.conflict_columns(on_conflict)
        rows = [self._write_row(e, conflict) for e in items]
        return self._batch.run(
            table=d.name, operation="upsert_many", rows=rows, decode=self._codec.decode,
            send=lambda chunk: self._run(
                "upsert_many", lambda: self._transport.upsert(d.name, d.schema, chunk, on_conflict),
                idempotent=True, category="batch",
            ),
            batch_size=size, mode=mode,
        )
