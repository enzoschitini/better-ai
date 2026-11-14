"""Repositório: idempotência declarada, logs sem valores, semântica A-01 (T-204)."""
from __future__ import annotations

import pytest

from bai_supabase.contracts.query import Condition, Op, Query
from bai_supabase.contracts.settings import TablesSettings
from bai_supabase.contracts.tables import TableDescriptor
from bai_supabase.errors.exceptions import (
    ConfigurationError,
    OperationTimeoutError,
    RecordNotFoundError,
    ServiceUnavailableError,
    UnexpectedError,
    ValidationError,
)
from tests.fakes.table_transport import InMemoryTableTransport, build_repository

D = TableDescriptor("docs", server_managed_columns=("id",))
SECRET = "SEGREDO-NO-VALOR"


def setup(descriptor=D, **kw):
    return build_repository(descriptor, **kw)


def test_idempotencia_e_categoria_por_metodo():
    repo, _, ex, _ = setup()
    rec = repo.insert({"title": "a", "slug": "a"})
    repo.insert_many([{"title": "b"}])
    repo.get_by_id(rec["id"]); repo.find(); repo.list(); list(repo.iterate())
    repo.update(rec["id"], {"title": "c"})
    repo.update_where(Condition("title", Op.EQ, "c"), {"title": "d"})
    repo.upsert({"title": "z"}, on_conflict="title")
    repo.upsert_many([{"title": "y"}], on_conflict="title")
    repo.delete(rec["id"])
    repo.delete_where(Condition("title", Op.EQ, "zz"))
    table = {o.name: (o.idempotent, o.category, o.resource) for o in ex.operations}
    assert table["table.insert"] == (False, "table", "docs")
    assert table["table.insert_many"] == (False, "batch", "docs")
    for name in ("get_by_id", "find", "list", "iterate", "update", "upsert", "delete"):
        assert table[f"table.{name}"][0] is True, name
    for name in ("update_where", "delete_where", "upsert_many"):
        assert table[f"table.{name}"][:2] == (True, "batch"), name


def test_logs_tem_tabela_duracao_contagem_e_nunca_valores():
    repo, _, _, log = setup()
    repo.insert({"title": SECRET, "slug": SECRET})
    repo.find(Query.eq("title", SECRET))
    assert log.events
    for level, event, fields in log.events:
        assert fields["table"] == "docs"
        assert SECRET not in repr((event, fields))
    done = [f for _, e, f in log.events if e == "operação de tabela concluída"]
    assert all("duration_ms" in f and "count" in f for f in done)
    assert {"INFO", "DEBUG"} >= set(log.levels())  # leituras DEBUG, escrita INFO


def test_not_found_sem_valor_e_sem_log_de_erro():
    repo, _, _, log = setup()
    with pytest.raises(RecordNotFoundError) as exc:
        repo.get_by_id(SECRET)
    assert SECRET not in str(exc.value) and exc.value.resource == "docs"
    assert "ERROR" not in log.levels()


def test_erro_do_executor_propaga_identico_e_nao_e_registrado_de_novo():
    repo, tr, _, log = setup()
    err = OperationTimeoutError("t", outcome_unknown=True)
    tr.fail_next("insert", err)
    with pytest.raises(OperationTimeoutError) as exc:
        repo.insert({"title": "a"})
    assert exc.value is err
    assert "ERROR" not in log.levels() and "WARNING" not in log.levels()


def test_insert_sem_retorno_do_servidor_e_erro():
    class Empty(InMemoryTableTransport):
        def insert(self, *a, **k):
            return []

    repo, *_ = setup(transport=Empty())
    with pytest.raises(UnexpectedError):
        repo.insert({"title": "a"})


def test_update_alteracoes_invalidas():
    repo, *_ = setup()
    rec = repo.insert({"title": "a"})
    for bad in ({}, {"id": "x"}, "texto"):
        with pytest.raises(ValidationError):
            repo.update(rec["id"], bad)  # type: ignore[arg-type]


def test_id_invalido_falha_antes_da_rede():
    repo, tr, *_ = setup()
    for call in (lambda: repo.get_by_id(None), lambda: repo.delete(""), lambda: repo.update(True, {"a": 1})):
        with pytest.raises(ValidationError):
            call()
    assert tr.calls == []


def test_descritor_invalido_ou_nao_permitido_falha_na_construcao():
    with pytest.raises(ConfigurationError):
        setup(TableDescriptor("bad name"))
    with pytest.raises(ConfigurationError):
        setup(settings=TablesSettings(allowlist=("outra",)))


def test_pk_gerenciada_permitida_no_upsert_por_pk():
    repo, *_ = setup()
    up = repo.upsert({"id": "fixo", "title": "a"})
    assert up["id"] == "fixo"
    assert repo.upsert({"id": "fixo", "title": "b"})["title"] == "b" and len(repo.find()) == 1


def test_iterate_valida_na_chamada_nao_na_primeira_leitura():
    repo, tr, *_ = setup()
    with pytest.raises(ValidationError):
        repo.iterate(Query.eq("a b", 1))
    assert tr.calls == []


def test_find_pagina_multiplas_vezes_com_ordem_por_pk():
    s = TablesSettings(default_page_size=2, max_page_size=2, server_max_rows=2)
    repo, tr, *_ = setup(settings=s)
    for i in range(5):
        repo.insert({"title": str(i)})
    assert len(repo.find()) == 5
    reqs = [r for r in tr.requests if r.limit == 2]
    assert len(reqs) == 3 and all(r.sorts[-1].column == "id" for r in reqs)
