"""Bateria de contrato de ``TableRepository`` (research/06 §13, A-01, FR-A1…A10).

Parametrizada por fábrica de repositório: hoje roda contra o transporte em memória; a
mesma bateria deve rodar contra o adapter real (projeto de teste) acrescentando uma
fábrica em ``FACTORIES``.
"""
from __future__ import annotations

from typing import Callable

import pytest

from src.database.supabase_integration.contracts.query import Condition, FilterGroup, Op, PageRequest, Query, Sort
from src.database.supabase_integration.contracts.results import DeleteResult
from src.database.supabase_integration.contracts.settings import TablesSettings
from src.database.supabase_integration.contracts.tables import BatchOptions, TableDescriptor
from src.database.supabase_integration.errors.exceptions import DuplicateRecordError, RecordNotFoundError, ValidationError
from src.database.supabase_integration.tests.fakes.table_transport import InMemoryTableTransport, build_repository


def _in_memory(descriptor: TableDescriptor, settings: TablesSettings):
    transport = InMemoryTableTransport()
    transport.configure(descriptor.name, schema=descriptor.schema, pk=descriptor.primary_key, unique=(("slug",),))
    repo, *_ = build_repository(descriptor, transport=transport, settings=settings)
    return repo


FACTORIES = {"in_memory": _in_memory}

DOCS = TableDescriptor("docs", server_managed_columns=("id",), sort_key="n")


@pytest.fixture(params=sorted(FACTORIES))
def make_repo(request) -> Callable[..., object]:
    factory = FACTORIES[request.param]

    def make(descriptor=None, settings=None):
        return factory(descriptor or DOCS, settings or TablesSettings())

    return make


def doc(n: int, **extra) -> dict:
    return {"n": n, "slug": f"s{n}", "title": f"t{n}", **extra}


def test_insert_devolve_valores_do_banco_e_get_by_id(make_repo):
    repo = make_repo()
    created = repo.insert(doc(1))
    assert created["id"] and created["title"] == "t1"
    assert repo.get_by_id(created["id"]) == created


def test_get_by_id_inexistente(make_repo):
    with pytest.raises(RecordNotFoundError):
        make_repo().get_by_id("nao-existe")


def test_find_sem_linhas_devolve_lista_vazia(make_repo):
    assert make_repo().find(Query.eq("title", "nada")) == []


def test_find_com_filtro_composto_ordem_e_colunas(make_repo):
    repo = make_repo()
    repo.insert_many([doc(i, status="a" if i % 2 else "b") for i in range(1, 7)])
    q = Query(
        filter=FilterGroup(logic="and", items=(
            Condition("status", Op.EQ, "a"),
            FilterGroup(logic="or", items=(Condition("n", Op.LT, 2), Condition("n", Op.GTE, 5))),
        )),
        sorts=(Sort("n", descending=True),),
        columns=("n",),
    )
    assert repo.find(q) == [{"n": 5}, {"n": 1}]


def test_insert_duplicado_levanta_erro_de_dominio(make_repo):
    repo = make_repo()
    repo.insert(doc(1))
    with pytest.raises(DuplicateRecordError):
        repo.insert(doc(1))


def test_update_e_update_inexistente(make_repo):
    repo = make_repo()
    rec = repo.insert(doc(1))
    updated = repo.update(rec["id"], {"title": "novo"})
    assert updated["title"] == "novo" and updated["slug"] == "s1"
    with pytest.raises(RecordNotFoundError):
        repo.update("nao-existe", {"title": "x"})


def test_update_where_devolve_contagem_e_recusa_filtro_vazio(make_repo):
    repo = make_repo()
    repo.insert_many([doc(i, status="a") for i in range(1, 4)])
    assert repo.update_where(Condition("status", Op.EQ, "a"), {"status": "b"}) == 3
    assert repo.update_where(Condition("status", Op.EQ, "zzz"), {"status": "b"}) == 0
    for empty in (None, FilterGroup()):
        with pytest.raises(ValidationError):
            repo.update_where(empty, {"status": "c"})


def test_delete_idempotente_e_delete_where(make_repo):
    repo = make_repo()
    rec = repo.insert(doc(1))
    assert repo.delete(rec["id"]) == DeleteResult(removed_count=1)
    assert repo.delete(rec["id"]) == DeleteResult(removed_count=0)  # inexistente: sem erro
    repo.insert_many([doc(i) for i in (2, 3)])
    assert repo.delete_where(Condition("n", Op.GT, 0)).removed_count == 2
    for empty in (None, FilterGroup()):
        with pytest.raises(ValidationError):
            repo.delete_where(empty)


def test_upsert_por_coluna_de_conflito(make_repo):
    repo = make_repo()
    rec = repo.insert(doc(1))
    up = repo.upsert(doc(1, title="mudou"), on_conflict="slug")
    assert up["id"] == rec["id"] and up["title"] == "mudou"
    new = repo.upsert(doc(2), on_conflict="slug")
    assert new["id"] != rec["id"] and len(repo.find()) == 2


def test_upsert_many_idempotente(make_repo):
    repo = make_repo()
    result = repo.upsert_many([doc(i) for i in range(1, 4)], on_conflict="slug")
    assert result.all_ok and result.total == 3
    result = repo.upsert_many([doc(i, title="x") for i in range(1, 4)], on_conflict="slug")
    assert result.all_ok and len(repo.find()) == 3


def test_lote_vazio_e_validacao_antes_da_rede(make_repo):
    repo = make_repo()
    for call in (lambda: repo.insert_many([]), lambda: repo.upsert_many([])):
        with pytest.raises(ValidationError):
            call()
    with pytest.raises(ValidationError):
        repo.insert_many([doc(1), {"n": 2, "id": "forçado"}])  # coluna gerenciada
    assert repo.find() == []  # nada foi enviado


def test_insert_many_resultado_por_item(make_repo):
    repo = make_repo()
    result = repo.insert_many([doc(i) for i in range(1, 6)], BatchOptions(batch_size=2))
    assert result.all_ok and [o.index for o in result.items] == [0, 1, 2, 3, 4]
    assert all(o.entity["id"] for o in result.items)


def test_insert_many_continue_isola_item_defeituoso(make_repo):
    repo = make_repo()
    repo.insert(doc(3))
    result = repo.insert_many([doc(1), doc(2), doc(3), doc(4)], BatchOptions(batch_size=4, mode="continue"))
    assert [o.ok for o in result.items] == [True, True, False, True]
    assert isinstance(result.items[2].error, DuplicateRecordError)
    assert len(repo.find()) == 4


def test_insert_many_stop_interrompe(make_repo):
    repo = make_repo()
    repo.insert(doc(3))
    result = repo.insert_many([doc(1), doc(3), doc(5), doc(6)], BatchOptions(batch_size=2, mode="stop"))
    assert result.stopped_early and result.failed == 2 and result.succeeded == 0
    assert len(repo.find()) == 1  # chunk 2 nunca enviado


def test_list_offset_com_contagem(make_repo):
    repo = make_repo()
    repo.insert_many([doc(i) for i in range(1, 8)])
    page = repo.list(Query(sorts=(Sort("n"),)), PageRequest(limit=3, offset=3, include_count=True))
    assert [r["n"] for r in page.items] == [4, 5, 6]
    assert page.total == 7 and page.has_more and page.offset == 3
    last = repo.list(Query(sorts=(Sort("n"),)), PageRequest(limit=3, offset=6))
    assert [r["n"] for r in last.items] == [7] and not last.has_more and last.total is None


def test_keyset_percorre_sem_repetir_nem_pular(make_repo):
    repo = make_repo()
    repo.insert_many([doc(i) for i in range(1, 11)])
    seen, cursor = [], "~start"
    while cursor:
        page = repo.list(None, PageRequest(limit=4, cursor=cursor))
        seen.extend(r["n"] for r in page.items)
        cursor = page.next_cursor
    assert seen == list(range(1, 11))


def test_iterate_e_find_nao_truncam_no_limite_do_servidor(make_repo):
    s = TablesSettings(default_page_size=3, max_page_size=3, server_max_rows=3)
    repo = make_repo(settings=s)
    repo.insert_many([doc(i) for i in range(1, 11)], BatchOptions(batch_size=3))
    assert [r["n"] for r in repo.iterate()] == list(range(1, 11))
    assert len(repo.find()) == 10
    plain = make_repo(TableDescriptor("sem_keyset", server_managed_columns=("id",)), s)
    plain.insert_many([doc(i) for i in range(1, 8)], BatchOptions(batch_size=3))
    assert len(list(plain.iterate())) == 7 == len(plain.find())


def test_colunas_desconhecidas_recusadas_com_allowlist(make_repo):
    repo = make_repo(TableDescriptor("docs", columns=("id", "n", "title", "slug"), server_managed_columns=("id",)))
    with pytest.raises(ValidationError):
        repo.insert({"n": 1, "slug": "a", "is_admin": True})
    with pytest.raises(ValidationError):
        repo.find(Query.eq("senha", "x"))
