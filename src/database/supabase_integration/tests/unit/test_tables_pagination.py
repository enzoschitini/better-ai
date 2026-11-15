"""Paginação offset/keyset, contagem, teto do servidor e varredura (T-205)."""
from __future__ import annotations

import base64
import json

import pytest

from bai_supabase.contracts.query import Condition, Op, PageRequest, Query, Sort
from bai_supabase.contracts.settings import TablesSettings
from bai_supabase.contracts.tables import BatchOptions, TableDescriptor
from bai_supabase.errors.exceptions import ServiceUnavailableError, ValidationError
from bai_supabase.tables.pagination import KEYSET_START
from tests.fakes.table_transport import InMemoryTableTransport, build_repository

KS = TableDescriptor("docs", server_managed_columns=("id",), sort_key="n")
PLAIN = TableDescriptor("docs", server_managed_columns=("id",))


def b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode()


def seeded(descriptor=KS, n=10, settings=None, max_rows=None):
    tr = InMemoryTableTransport(max_rows=max_rows)
    settings = settings or TablesSettings()
    repo, _, _, log = build_repository(descriptor, transport=tr, settings=settings)
    repo.insert_many([{"n": i, "g": i % 2} for i in range(1, n + 1)], BatchOptions(batch_size=min(500, settings.server_max_rows)))
    tr.requests.clear()
    return repo, tr, log


def test_offset_padrao_has_more_por_item_extra():
    repo, tr, _ = seeded(PLAIN)
    page = repo.list(None, PageRequest(limit=4))
    assert len(page.items) == 4 and page.has_more and page.next_cursor is None and page.total is None
    assert tr.requests[0].limit == 5 and tr.requests[0].count is None  # +1, sem contagem por padrão
    assert not repo.list(None, PageRequest(limit=10)).has_more


def test_contagem_so_quando_pedida_e_sobrepoe_has_more():
    repo, tr, _ = seeded(PLAIN)
    page = repo.list(None, PageRequest(limit=4, offset=8, include_count=True))
    assert page.total == 10 and not page.has_more and tr.requests[0].count == "exact"


def test_ordem_sempre_termina_na_pk():
    repo, tr, _ = seeded(PLAIN)
    repo.list(Query(sorts=(Sort("n", descending=True),)))
    assert [s.column for s in tr.requests[0].sorts] == ["n", "id"]
    repo.list(Query(sorts=(Sort("id"),)))
    assert [s.column for s in tr.requests[1].sorts] == ["id"]


def test_page_size_acima_do_teto_e_reduzido_com_warning():
    s = TablesSettings(max_page_size=1000, server_max_rows=5)
    repo, tr, log = seeded(PLAIN, settings=s)
    page = repo.list(None, PageRequest(limit=5000))
    assert page.limit == 5 and len(page.items) == 5 and page.has_more
    assert "WARNING" in log.levels()
    assert tr.requests[0].limit == 5  # nunca pede mais que o servidor entrega


def test_page_size_e_offset_invalidos():
    repo, *_ = seeded(PLAIN)
    for bad in (PageRequest(limit=0), PageRequest(limit=-1), PageRequest(offset=-1)):
        with pytest.raises(ValidationError):
            repo.list(None, bad)


def test_keyset_cursor_opaco_e_contagem_so_na_primeira_pagina():
    repo, tr, _ = seeded()
    first = repo.list(None, PageRequest(limit=4, cursor=KEYSET_START, include_count=True))
    assert [r["n"] for r in first.items] == [1, 2, 3, 4] and first.total == 10 and first.has_more
    second = repo.list(None, PageRequest(limit=4, cursor=first.next_cursor, include_count=True))
    assert [r["n"] for r in second.items] == [5, 6, 7, 8] and second.total is None
    assert tr.requests[1].count is None
    assert '"k"' not in first.next_cursor  # opaco (base64), não texto legível


def test_keyset_descendente_e_com_filtro():
    repo, *_ = seeded()
    q = Query(filter=Condition("g", Op.EQ, 1), sorts=(Sort("n", descending=True),))
    seen, cur = [], KEYSET_START
    while cur:
        p = repo.list(q, PageRequest(limit=2, cursor=cur))
        seen += [r["n"] for r in p.items]
        cur = p.next_cursor
    assert seen == [9, 7, 5, 3, 1]


def test_keyset_estavel_com_insercao_concorrente():
    repo, tr, _ = seeded()
    p1 = repo.list(None, PageRequest(limit=3, cursor=KEYSET_START))
    repo.insert({"n": 0})  # entra ANTES do cursor: não repete nem desloca o que vem depois
    repo.insert({"n": 11})
    p2 = repo.list(None, PageRequest(limit=3, cursor=p1.next_cursor))
    assert [r["n"] for r in p2.items] == [4, 5, 6]


def test_keyset_empate_na_chave_usa_pk():
    tr = InMemoryTableTransport()
    repo, *_ = build_repository(KS, transport=tr)
    repo.insert_many([{"n": 1, "x": i} for i in range(5)])
    seen, cur = [], KEYSET_START
    while cur:
        p = repo.list(None, PageRequest(limit=2, cursor=cur))
        seen += [r["id"] for r in p.items]
        cur = p.next_cursor
    assert len(seen) == 5 and len(set(seen)) == 5


def test_cursor_invalido_adulterado_e_de_outra_consulta():
    repo, *_ = seeded()
    p = repo.list(None, PageRequest(limit=2, cursor=KEYSET_START))
    for bad in ("lixo!!", b64(b"{}"), b64(b'{"v":9}')):
        with pytest.raises(ValidationError):
            repo.list(None, PageRequest(cursor=bad))
    with pytest.raises(ValidationError):  # cursor reutilizado com outro filtro
        repo.list(Query.eq("g", 1), PageRequest(cursor=p.next_cursor))
    forged = json.loads(base64.urlsafe_b64decode(p.next_cursor + "=="))
    forged["k"] = {"x": 1}
    with pytest.raises(ValidationError):
        repo.list(None, PageRequest(cursor=b64(json.dumps(forged).encode())))


def test_keyset_exige_sort_key_e_ordenacao_compativel():
    repo, *_ = seeded(PLAIN)
    with pytest.raises(ValidationError):
        repo.list(None, PageRequest(cursor=KEYSET_START))
    repo2, *_ = seeded()
    for sorts in ((Sort("g"),), (Sort("n"), Sort("id", descending=True)), (Sort("n", nulls_first=True),)):
        with pytest.raises(ValidationError):
            repo2.list(Query(sorts=sorts), PageRequest(cursor=KEYSET_START))
    assert repo2.list(Query(sorts=(Sort("n"), Sort("id"))), PageRequest(cursor=KEYSET_START))


def test_keyset_projecao_mantem_chave_so_internamente():
    repo, tr, _ = seeded()
    p = repo.list(Query(columns=("g",)), PageRequest(limit=2, cursor=KEYSET_START))
    assert p.items == [{"g": 1}, {"g": 0}] and p.next_cursor
    assert set(tr.requests[0].columns) == {"g", "n", "id"}


def test_iterate_usa_keyset_e_nao_trunca_no_limite_do_servidor():
    s = TablesSettings(default_page_size=3, max_page_size=3, server_max_rows=3)
    repo, tr, _ = seeded(settings=s, max_rows=3, n=10)
    assert [r["n"] for r in repo.iterate()] == list(range(1, 11))
    assert all(r.offset == 0 for r in tr.requests)  # keyset, sem offset
    # página cheia nunca é tomada como fim: 9 itens = 3 páginas cheias + 1 leitura vazia
    repo2, tr2, _ = seeded(settings=s, max_rows=3, n=9)
    assert len(list(repo2.iterate())) == 9 and len(tr2.requests) == 4


def test_iterate_offset_quando_ordenacao_nao_e_compativel_com_keyset():
    repo, tr, _ = seeded()
    got = list(repo.iterate(Query(sorts=(Sort("g"),)), page_size=4))
    assert len(got) == 10 and any(r.offset > 0 for r in tr.requests)


def test_iterate_e_preguicoso_uma_pagina_por_vez():
    repo, tr, _ = seeded(n=10)
    it = repo.iterate(page_size=3)
    assert tr.requests == []
    next(it)
    assert len(tr.requests) == 1
    for _ in range(3):
        next(it)
    assert len(tr.requests) == 2


def test_falha_no_meio_traz_ultimo_cursor_bom_e_retoma():
    repo, tr, _ = seeded(n=9)
    it = repo.iterate(page_size=3)
    got = [next(it)["n"] for _ in range(3)]
    tr.fail_next("select", ServiceUnavailableError("fora"))
    with pytest.raises(ServiceUnavailableError) as exc:
        got += [r["n"] for r in it]
    assert got == [1, 2, 3]
    cursor = exc.value.resume_cursor
    assert cursor
    assert [r["n"] for r in repo.iterate(page_size=3, start_after=cursor)] == [4, 5, 6, 7, 8, 9]


def test_start_after_exige_keyset():
    repo, *_ = seeded(PLAIN)
    with pytest.raises(ValidationError):
        list(repo.iterate(start_after="x"))
