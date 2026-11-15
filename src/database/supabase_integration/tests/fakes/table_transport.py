"""Transporte de tabelas em memória: imita PostgREST (filtros, ordem, offset/limit, count,
upsert, teto de linhas ``max_rows``) e levanta erros de DOMÍNIO."""
from __future__ import annotations

import copy
import re
import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Optional, Sequence

from bai_supabase.contracts.query import Condition, Filter, FilterGroup, Op, Sort, is_empty_filter
from bai_supabase.contracts.transports import SelectRequest, SelectResponse
from bai_supabase.errors.exceptions import DuplicateRecordError, SupabaseIntegrationError, ValidationError


class _Table:
    def __init__(self, pk: str, unique: tuple, autogen: dict) -> None:
        self.pk = pk
        self.unique = unique
        self.autogen = autogen
        self.rows: list[dict] = []


def _pair(a: Any, b: Any) -> tuple:
    """Alinha tipos para comparar (número x texto numérico; datas ISO)."""
    if isinstance(a, str) and isinstance(b, str):
        try:
            return datetime.fromisoformat(a), datetime.fromisoformat(b)
        except ValueError:
            return a, b
    if isinstance(a, str) != isinstance(b, str) and not isinstance(a, bool) and not isinstance(b, bool):
        try:
            return Decimal(str(a)), Decimal(str(b))
        except InvalidOperation:
            return a, b
    return a, b


def _like(value: Any, pattern: str, ci: bool) -> bool:
    if not isinstance(value, str):
        return False
    regex = "^" + "".join(".*" if c in "%*" else "." if c == "_" else re.escape(c) for c in pattern) + "$"
    return re.match(regex, value, re.IGNORECASE | re.DOTALL if ci else re.DOTALL) is not None


class InMemoryTableTransport:
    """Cumpre ``TableTransport``. ``calls`` registra (método, tabela) para asserções."""

    def __init__(self, *, max_rows: Optional[int] = None) -> None:
        self.max_rows = max_rows
        self.calls: list[tuple[str, str]] = []
        self.requests: list[SelectRequest] = []
        self._tables: dict[tuple[str, str], _Table] = {}
        self._failures: list[tuple[str, Callable[[Sequence[dict]], bool], SupabaseIntegrationError]] = []

    # ------------------------------------------------------------------ configuração
    def configure(self, table: str, *, schema: str = "public", pk: str = "id", unique: tuple = (),
                  autogen: Optional[dict] = None) -> None:
        """``unique``: tuplas de colunas únicas. ``autogen``: coluna -> callable (preenche se ausente)."""
        gen = {pk: lambda: str(uuid.uuid4())} if autogen is None else autogen
        self._tables[(schema, table)] = _Table(pk, tuple(unique), gen)

    def seed(self, table: str, rows: Sequence[dict], *, schema: str = "public") -> None:
        self._get(table, schema).rows.extend(copy.deepcopy(list(rows)))

    def rows(self, table: str, *, schema: str = "public") -> list[dict]:
        return copy.deepcopy(self._get(table, schema).rows)

    def fail_when(self, method: str, predicate: Callable[[Sequence[dict]], bool], error: SupabaseIntegrationError) -> None:
        """Levanta ``error`` em ``method`` (insert/upsert/select/...) quando ``predicate(rows)``."""
        self._failures.append((method, predicate, error))

    def fail_next(self, method: str, error: SupabaseIntegrationError, times: int = 1) -> None:
        state = {"n": times}

        def predicate(_rows: Sequence[dict]) -> bool:
            state["n"] -= 1
            return state["n"] >= 0

        self._failures.append((method, predicate, error))

    def _get(self, table: str, schema: str) -> _Table:
        return self._tables.setdefault((schema, table), _Table("id", (), {"id": lambda: str(uuid.uuid4())}))

    def _maybe_fail(self, method: str, rows: Sequence[dict]) -> None:
        for m, predicate, error in self._failures:
            if m == method and predicate(rows):
                raise error

    # ------------------------------------------------------------------ filtros
    def _match(self, row: dict, node: Optional[Filter]) -> bool:
        if node is None:
            return True
        if isinstance(node, FilterGroup):
            items = [i for i in node.items if not is_empty_filter(i)]
            if not items:
                return True
            fn = all if node.logic == "and" else any
            return fn(self._match(row, i) for i in items)
        return self._cond(row, node)

    @staticmethod
    def _cond(row: dict, c: Condition) -> bool:
        v = row.get(c.column)
        if c.op is Op.IS_NULL:
            return v is None
        if c.op is Op.NOT_NULL:
            return v is not None
        if c.op is Op.IN:
            return v is not None and any(_pair(v, x)[0] == _pair(v, x)[1] for x in c.value)
        if c.op in (Op.LIKE, Op.ILIKE):
            return _like(v, c.value, c.op is Op.ILIKE)
        if c.op is Op.CONTAINS:
            if isinstance(v, list):
                return all(x in v for x in (c.value if isinstance(c.value, list) else [c.value]))
            if isinstance(v, dict) and isinstance(c.value, dict):
                return all(k in v and v[k] == x for k, x in c.value.items())
            return False
        if v is None:
            return c.op is Op.NEQ  # NULL <> x é desconhecido no SQL; aqui ignoramos
        a, b = _pair(v, c.value)
        return {Op.EQ: a == b, Op.NEQ: a != b, Op.GT: a > b, Op.GTE: a >= b, Op.LT: a < b, Op.LTE: a <= b}[c.op]

    # ------------------------------------------------------------------ ordenação
    def _sorted(self, rows: list[dict], sorts: Sequence[Sort]) -> list[dict]:
        out = list(rows)
        for s in reversed(sorts):  # estável: do critério menos ao mais significativo
            nulls_first = s.nulls_first if s.nulls_first is not None else s.descending  # padrão do Postgres
            present = [r for r in out if r.get(s.column) is not None]
            nulls = [r for r in out if r.get(s.column) is None]
            present.sort(key=lambda r: _SortKey(r[s.column]), reverse=s.descending)
            out = nulls + present if nulls_first else present + nulls
        return out

    # ------------------------------------------------------------------ TableTransport
    def select(self, req: SelectRequest) -> SelectResponse:
        self.calls.append(("select", req.table))
        self.requests.append(req)
        self._maybe_fail("select", [])
        t = self._get(req.table, req.schema)
        matched = self._sorted([r for r in t.rows if self._match(r, req.filter)], req.sorts)
        total = len(matched) if req.count else None
        window = matched[req.offset:]
        if req.limit is not None:
            window = window[: req.limit]
        if self.max_rows is not None:
            window = window[: self.max_rows]  # truncamento silencioso do servidor
        cols = req.columns
        rows = [{k: copy.deepcopy(v) for k, v in r.items() if cols is None or k in cols} for r in window]
        return SelectResponse(rows=rows, count=total)

    def _fill(self, t: _Table, row: dict) -> dict:
        new = copy.deepcopy(row)
        for col, gen in t.autogen.items():
            if new.get(col) is None:
                new[col] = gen()
        return new

    def _check_unique(self, t: _Table, rows: Sequence[dict], existing: list[dict]) -> None:
        keys = [(t.pk,)] + [tuple(u) for u in t.unique]
        seen = list(existing)
        for row in rows:
            for cols in keys:
                if any(row.get(c) is None for c in cols):
                    continue
                if any(all(o.get(c) == row.get(c) for c in cols) for o in seen):
                    raise DuplicateRecordError("violação de unicidade", operation="table.insert", resource="fake")
            seen.append(row)

    def insert(self, table: str, schema: str, rows: Sequence[dict]) -> list[dict]:
        self.calls.append(("insert", table))
        self._maybe_fail("insert", rows)
        t = self._get(table, schema)
        filled = [self._fill(t, r) for r in rows]
        self._check_unique(t, filled, t.rows)  # atômico: nada é gravado se falhar
        t.rows.extend(filled)
        return copy.deepcopy(filled)

    def upsert(self, table: str, schema: str, rows: Sequence[dict], on_conflict: Optional[str] = None,
               ignore_duplicates: bool = False) -> list[dict]:
        self.calls.append(("upsert", table))
        self._maybe_fail("upsert", rows)
        t = self._get(table, schema)
        cols = [c.strip() for c in on_conflict.split(",")] if on_conflict else [t.pk]
        out: list[dict] = []
        for row in rows:
            existing = next((r for r in t.rows if all(r.get(c) == row.get(c) for c in cols) and all(row.get(c) is not None for c in cols)), None)
            if existing is None:
                new = self._fill(t, row)
                t.rows.append(new)
                out.append(copy.deepcopy(new))
            elif not ignore_duplicates:
                existing.update(copy.deepcopy(row))
                out.append(copy.deepcopy(existing))
        return out

    def update(self, table: str, schema: str, changes: dict, filter: Filter) -> list[dict]:
        self.calls.append(("update", table))
        if is_empty_filter(filter):
            raise ValidationError("update sem filtro")
        self._maybe_fail("update", [changes])
        t = self._get(table, schema)
        hit = [r for r in t.rows if self._match(r, filter)]
        for r in hit:
            r.update(copy.deepcopy(changes))
        return copy.deepcopy(hit)

    def delete(self, table: str, schema: str, filter: Filter) -> list[dict]:
        self.calls.append(("delete", table))
        if is_empty_filter(filter):
            raise ValidationError("delete sem filtro")
        self._maybe_fail("delete", [])
        t = self._get(table, schema)
        hit = [r for r in t.rows if self._match(r, filter)]
        t.rows = [r for r in t.rows if r not in hit]
        return copy.deepcopy(hit)


class _SortKey:
    """Chave comparável para valores mistos (numérico x texto numérico, datas ISO)."""

    def __init__(self, value: Any) -> None:
        self.value = value

    def __lt__(self, other: "_SortKey") -> bool:
        a, b = _pair(self.value, other.value)
        return a < b


def build_repository(descriptor, *, transport=None, settings=None, executor=None, logger=None, **kwargs):
    """Monta um ``PostgresTableRepository`` com fakes. Devolve ``(repo, transport, executor, logger)``."""
    from bai_supabase.contracts.settings import TablesSettings
    from bai_supabase.tables.repository import PostgresTableRepository
    from tests.fakes.executor import PassThroughExecutor
    from tests.fakes.logger import CaptureLogger

    transport = transport or InMemoryTableTransport()
    executor = executor or PassThroughExecutor()
    logger = logger or CaptureLogger()
    settings = settings or TablesSettings()
    repo = PostgresTableRepository(descriptor, transport, executor, logger, settings, **kwargs)
    return repo, transport, executor, logger
