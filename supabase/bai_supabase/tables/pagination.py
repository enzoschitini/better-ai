"""Paginação e varredura (research/09 §4-§7, decisão C-2).

Offset/limit é o padrão. Keyset é OPCIONAL: só quando o descritor declara ``sort_key``
(estável e NÃO nula) e o chamador pede (``PageRequest.cursor``; ``KEYSET_START`` abre a
cadeia). Ordenação sempre determinística (PK como desempate). Nenhuma leitura é
truncada em silêncio pelo ``max-rows`` do servidor: o teto de página é
``min(max_page_size, server_max_rows)`` e a varredura continua até uma página curta.
"""

from __future__ import annotations

import base64
import hashlib
import json
from typing import Any, Callable, Iterator, Optional

from bai_supabase.contracts.logging import LoggerContract
from bai_supabase.contracts.query import Condition, Filter, FilterGroup, Op, Page, PageRequest, Query, Sort
from bai_supabase.contracts.settings import TablesSettings
from bai_supabase.contracts.tables import TableDescriptor
from bai_supabase.contracts.transports import SelectRequest, SelectResponse
from bai_supabase.errors.exceptions import SupabaseIntegrationError, ValidationError

#: Cursor sentinela que abre uma cadeia keyset (não é base64: sem colisão com cursores reais).
KEYSET_START = "~start"
CURSOR_VERSION = 1
HIGH_OFFSET_WARNING = 10_000

Fetch = Callable[[SelectRequest], SelectResponse]


class Paginator:
    """Monta requisições paginadas e interpreta as respostas; não conhece o transporte."""

    def __init__(self, descriptor: TableDescriptor, settings: TablesSettings, logger: LoggerContract) -> None:
        self._d = descriptor
        self._s = settings
        self._log = logger

    @property
    def keyset_available(self) -> bool:
        return self._d.sort_key is not None

    # ------------------------------------------------------------------ tamanhos
    def page_size(self, requested: Optional[int]) -> int:
        """Tamanho efetivo: padrão da config; acima do teto é reduzido com WARNING."""
        if requested is None:
            requested = self._s.default_page_size
        if isinstance(requested, bool) or not isinstance(requested, int) or requested < 1:
            raise ValidationError("tamanho de página deve ser inteiro >= 1", resource=self._d.name)
        ceiling = min(self._s.max_page_size, self._s.server_max_rows)
        if requested > ceiling:
            self._log.warning(
                "tamanho de página reduzido ao teto", table=self._d.name, requested=requested, effective=ceiling
            )
            return ceiling
        return requested

    # ------------------------------------------------------------------ ordenação
    def _offset_sorts(self, query: Query) -> tuple[Sort, ...]:
        sorts = query.sorts
        if not any(s.column == self._d.primary_key for s in sorts):
            sorts = sorts + (Sort(self._d.primary_key),)
        return sorts

    def _keyset_direction(self, query: Query) -> Optional[bool]:
        """Direção do keyset (True = decrescente) ou None se a ordenação não for compatível.

        Compatível: sem ordenação, ou ``sort_key`` [+ PK na mesma direção], sem ``nulls_first``.
        """
        if not query.sorts:
            return False
        first, rest = query.sorts[0], query.sorts[1:]
        if first.column != self._d.sort_key or first.nulls_first is not None:
            return None
        if rest and not (
            len(rest) == 1
            and rest[0].column == self._d.primary_key
            and rest[0].descending == first.descending
            and rest[0].nulls_first is None
        ):
            return None
        return first.descending

    def _keyset_desc(self, query: Query) -> bool:
        direction = self._keyset_direction(query)
        if direction is None:
            raise ValidationError(
                "keyset exige ordenação por sort_key (e PK, na mesma direção)", resource=self._d.name
            )
        return direction

    # ------------------------------------------------------------------ cursor
    def _signature(self, query: Query, desc: bool) -> str:
        raw = repr((self._d.schema, self._d.name, query.filter, desc))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]

    def _encode_cursor(self, sig: str, sort_value: Any, pk_value: Any) -> str:
        payload = {"v": CURSOR_VERSION, "s": sig, "k": sort_value, "p": pk_value}
        raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")

    def _decode_cursor(self, cursor: str, sig: str) -> tuple[Any, Any]:
        try:
            raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4))
            payload = json.loads(raw.decode("utf-8"))
            ok = isinstance(payload, dict) and payload.get("v") == CURSOR_VERSION
        except Exception:  # noqa: BLE001 - qualquer lixo vira ValidationError
            ok = False
        if not ok:
            raise ValidationError("cursor inválido", resource=self._d.name)
        if payload.get("s") != sig:
            raise ValidationError("cursor não pertence a esta consulta", resource=self._d.name)
        key, pk = payload.get("k"), payload.get("p")
        for value in (key, pk):
            if value is None or isinstance(value, (dict, list, bool)):
                raise ValidationError("cursor inválido", resource=self._d.name)
        return key, pk

    def _after_filter(self, base: Optional[Filter], desc: bool, key: Any, pk: Any) -> Filter:
        """``k > k0 OR (k = k0 AND pk > p0)`` (``<`` em ordem decrescente), AND o filtro do usuário."""
        op = Op.LT if desc else Op.GT
        sk, pkc = self._d.sort_key, self._d.primary_key
        after = FilterGroup(
            logic="or",
            items=(
                Condition(sk, op, key),  # type: ignore[arg-type]
                FilterGroup(logic="and", items=(Condition(sk, Op.EQ, key), Condition(pkc, op, pk))),  # type: ignore[arg-type]
            ),
        )
        return after if base is None else FilterGroup(logic="and", items=(base, after))

    def _cursor_from_row(self, sig: str, row: dict) -> str:
        key, pk = row.get(self._d.sort_key), row.get(self._d.primary_key)  # type: ignore[arg-type]
        if key is None or pk is None:
            raise ValidationError("keyset exige sort_key e PK não nulos", resource=self._d.name)
        return self._encode_cursor(sig, key, pk)

    # ------------------------------------------------------------------ montagem
    def _keyset_columns(self, query: Query) -> tuple[Optional[tuple[str, ...]], frozenset[str]]:
        """Garante sort_key e PK no select do keyset; devolve o que remover depois."""
        if query.columns is None:
            return None, frozenset()
        needed = {self._d.sort_key, self._d.primary_key} - set(query.columns)
        return query.columns + tuple(sorted(needed)), frozenset(needed)  # type: ignore[arg-type]

    @staticmethod
    def _strip(rows: list[dict], names: frozenset[str]) -> list[dict]:
        if not names:
            return rows
        return [{k: v for k, v in row.items() if k not in names} for row in rows]

    def _request(self, query: Query, *, columns, filter_, sorts, limit, offset, count) -> SelectRequest:
        return SelectRequest(
            table=self._d.name,
            schema=self._d.schema,
            columns=columns,
            filter=filter_,
            sorts=sorts,
            limit=limit,
            offset=offset,
            count=count,
        )

    # ------------------------------------------------------------------ página única
    def list_page(self, fetch: Fetch, query: Query, page: PageRequest) -> Page:
        """Uma página (linhas ``dict``). ``cursor`` presente = keyset; senão offset."""
        size = self.page_size(page.limit)
        fetch_limit = min(size + 1, self._s.server_max_rows)
        peek = fetch_limit > size  # sabemos distinguir "há mais" pelo item extra
        if page.cursor is not None:
            return self._keyset_page(fetch, query, page, size, fetch_limit, peek)
        offset = page.offset
        if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
            raise ValidationError("offset deve ser inteiro >= 0", resource=self._d.name)
        if offset >= HIGH_OFFSET_WARNING:
            self._log.warning("offset alto: prefira keyset", table=self._d.name, offset=offset)
        req = self._request(
            query,
            columns=query.columns,
            filter_=query.filter,
            sorts=self._offset_sorts(query),
            limit=fetch_limit,
            offset=offset,
            count="exact" if page.include_count else None,
        )
        resp = fetch(req)
        rows = list(resp.rows)
        has_more = len(rows) > size if peek else len(rows) >= size
        rows = rows[:size]
        total = resp.count if page.include_count else None
        if total is not None:
            has_more = offset + len(rows) < total
        return Page(items=rows, limit=size, offset=offset, total=total, has_more=has_more)

    def _keyset_page(self, fetch: Fetch, query: Query, page: PageRequest, size: int, fetch_limit: int, peek: bool) -> Page:
        if not self.keyset_available:
            raise ValidationError("keyset indisponível: o descritor não declara sort_key", resource=self._d.name)
        desc = self._keyset_desc(query)
        sig = self._signature(query, desc)
        start = page.cursor == KEYSET_START
        filter_ = query.filter
        if not start:
            key, pk = self._decode_cursor(page.cursor, sig)  # type: ignore[arg-type]
            filter_ = self._after_filter(query.filter, desc, key, pk)
        columns, extra = self._keyset_columns(query)
        sorts = (Sort(self._d.sort_key, desc), Sort(self._d.primary_key, desc))  # type: ignore[arg-type]
        count = "exact" if (page.include_count and start) else None  # contagem só na primeira página
        resp = fetch(self._request(query, columns=columns, filter_=filter_, sorts=sorts, limit=fetch_limit, offset=0, count=count))
        rows = list(resp.rows)
        has_more = len(rows) > size if peek else len(rows) >= size
        rows = rows[:size]
        next_cursor = self._cursor_from_row(sig, rows[-1]) if has_more and rows else None
        return Page(
            items=self._strip(rows, extra),
            limit=size,
            offset=0,
            next_cursor=next_cursor,
            total=resp.count if count else None,
            has_more=has_more,
        )

    # ------------------------------------------------------------------ varredura
    def scan(
        self, fetch: Fetch, query: Query, page_size: Optional[int] = None, start_after: Optional[str] = None
    ) -> Iterator[list[dict]]:
        """Gera páginas de linhas, uma por vez (memória constante). Keyset se houver ``sort_key``.

        Para quando uma página vem com menos linhas que o pedido; página cheia sempre
        provoca nova leitura (nunca assume que acabou no limite do servidor). Em falha,
        a exceção recebe ``resume_cursor`` (último cursor bom; só em keyset).
        """
        size = self.page_size(page_size)
        if self.keyset_available and self._keyset_direction(query) is not None:
            yield from self._scan_keyset(fetch, query, size, start_after)
            return
        if start_after is not None:
            raise ValidationError("start_after exige keyset (descritor sem sort_key)", resource=self._d.name)
        yield from self._scan_offset(fetch, query, size)

    def _scan_offset(self, fetch: Fetch, query: Query, size: int) -> Iterator[list[dict]]:
        sorts = self._offset_sorts(query)
        offset, number = 0, 0
        while True:
            resp = fetch(self._request(query, columns=query.columns, filter_=query.filter, sorts=sorts, limit=size, offset=offset, count=None))
            rows = list(resp.rows)
            number += 1
            self._log.debug("página lida", table=self._d.name, page=number, count=len(rows), mode="offset")
            if rows:
                yield rows
            if len(rows) < size:
                return
            offset += len(rows)

    def _scan_keyset(self, fetch: Fetch, query: Query, size: int, start_after: Optional[str]) -> Iterator[list[dict]]:
        desc = self._keyset_desc(query)
        sig = self._signature(query, desc)
        columns, extra = self._keyset_columns(query)
        sorts = (Sort(self._d.sort_key, desc), Sort(self._d.primary_key, desc))  # type: ignore[arg-type]
        cursor: Optional[str] = None
        filter_ = query.filter
        if start_after is not None and start_after != KEYSET_START:
            cursor = start_after
            filter_ = self._after_filter(query.filter, desc, *self._decode_cursor(start_after, sig))
        number = 0
        while True:
            try:
                resp = fetch(self._request(query, columns=columns, filter_=filter_, sorts=sorts, limit=size, offset=0, count=None))
            except SupabaseIntegrationError as exc:
                exc.resume_cursor = cursor  # type: ignore[attr-defined]
                raise
            rows = list(resp.rows)
            number += 1
            self._log.debug("página lida", table=self._d.name, page=number, count=len(rows), mode="keyset")
            if rows:
                cursor = self._cursor_from_row(sig, rows[-1])
                yield self._strip(rows, extra)
            if len(rows) < size:
                return
            filter_ = self._after_filter(query.filter, desc, *self._decode_cursor(cursor, sig))  # type: ignore[arg-type]


__all__ = ["KEYSET_START", "Paginator", "Fetch"]
