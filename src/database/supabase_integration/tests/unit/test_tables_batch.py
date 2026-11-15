"""Lote: chunks, stop/continue, isolamento, sem retry em insert puro (T-206)."""
from __future__ import annotations

import pytest

from src.database.supabase_integration.contracts.resilience import Operation
from src.database.supabase_integration.contracts.settings import TablesSettings
from src.database.supabase_integration.contracts.tables import BatchOptions, TableDescriptor
from src.database.supabase_integration.errors.exceptions import (
    DataError,
    DuplicateRecordError,
    MappingError,
    OperationTimeoutError,
    ValidationError,
)
from src.database.supabase_integration.tables.batch import BatchRunner
from src.database.supabase_integration.tests.fakes.logger import CaptureLogger
from src.database.supabase_integration.tests.fakes.table_transport import InMemoryTableTransport, build_repository

D = TableDescriptor("docs", server_managed_columns=("id",))


def rows(n):
    return [{"n": i} for i in range(n)]


def test_chunking_por_batch_size_e_indices_originais():
    repo, tr, *_ = build_repository(D)
    result = repo.insert_many(rows(7), BatchOptions(batch_size=3))
    assert [c for c in tr.calls if c[0] == "insert"] == [("insert", "docs")] * 3
    assert [o.index for o in result.items] == list(range(7)) and result.all_ok


def test_batch_size_acima_do_teto_e_erro_nao_ajuste():
    repo, tr, *_ = build_repository(D)
    with pytest.raises(ValidationError):
        repo.insert_many(rows(3), BatchOptions(batch_size=1001))
    assert tr.calls == []


def test_usa_batch_size_da_configuracao():
    repo, tr, *_ = build_repository(D, settings=TablesSettings(batch_size=2))
    repo.insert_many(rows(5))
    assert len(tr.calls) == 3


def test_erro_transitorio_nao_dispara_bisseccao_e_marca_chunk():
    repo, tr, *_ = build_repository(D)
    err = OperationTimeoutError("t", outcome_unknown=True)
    tr.fail_next("insert", err)
    result = repo.insert_many(rows(4), BatchOptions(batch_size=2, mode="continue"))
    assert [o.ok for o in result.items] == [False, False, True, True]
    assert result.items[0].error is err
    assert len(tr.calls) == 2  # sem reenvio de itens do chunk que falhou


def test_bisseccao_so_para_erro_de_dados_com_envio_minimo():
    repo, tr, *_ = build_repository(D)
    tr.fail_when("insert", lambda rs: any(r.get("n") == 5 for r in rs), DataError("ruim"))
    result = repo.insert_many(rows(8), BatchOptions(batch_size=8))
    assert [i for i, o in enumerate(result.items) if not o.ok] == [5]
    assert len(repo.find()) == 7
    assert len(tr.calls) < 8 + 1  # bem menos que reenviar item a item + chunk


def test_stop_nao_isola_e_marca_stopped_early():
    repo, tr, *_ = build_repository(D)
    tr.fail_when("insert", lambda rs: any(r.get("n") == 1 for r in rs), DataError("ruim"))
    result = repo.insert_many(rows(6), BatchOptions(batch_size=2, mode="stop"))
    assert result.stopped_early and (result.succeeded, result.failed) == (0, 2) and len(tr.calls) == 1


def test_stop_na_ultimo_chunk_nao_marca_stopped_early():
    repo, tr, *_ = build_repository(D)
    tr.fail_when("insert", lambda rs: any(r.get("n") == 3 for r in rs), DataError("ruim"))
    result = repo.insert_many(rows(4), BatchOptions(batch_size=2, mode="stop"))
    assert not result.stopped_early and result.failed == 2 and not result.all_ok


def test_isolamento_pode_ser_desligado():
    repo, tr, *_ = build_repository(D, isolate_failures=False)
    tr.fail_when("insert", lambda rs: any(r.get("n") == 1 for r in rs), DataError("ruim"))
    result = repo.insert_many(rows(4), BatchOptions(batch_size=4))
    assert result.failed == 4 and len(tr.calls) == 1


def test_insert_nao_idempotente_e_upsert_idempotente_no_executor():
    repo, _, ex, _ = build_repository(D)
    repo.insert_many(rows(2))
    repo.upsert_many([{"id": "a", "n": 1}], on_conflict="id")
    ops: list[Operation] = ex.operations
    assert (ops[0].name, ops[0].idempotent, ops[0].category) == ("table.insert_many", False, "batch")
    assert (ops[1].name, ops[1].idempotent) == ("table.upsert_many", True)


def test_executor_e_chamado_por_chunk_e_retry_fica_com_ele():
    repo, tr, ex, _ = build_repository(D)
    repo.upsert_many([{"id": str(i), "n": i} for i in range(5)], on_conflict="id", options=BatchOptions(batch_size=2))
    assert len(ex.operations) == 3


def test_logs_do_lote_sem_valores_e_sem_linha_por_item():
    repo, tr, _, log = build_repository(D)
    tr.fail_when("insert", lambda rs: any(r.get("n") == 1 for r in rs), DuplicateRecordError("dup"))
    repo.insert_many([{"n": i, "segredo": "VALOR-SECRETO"} for i in range(30)], BatchOptions(batch_size=3))
    events = [e for _, e, _ in log.events]
    assert events.count("lote iniciado") == 1 and events.count("lote concluído") == 1
    assert 1 <= events.count("progresso do lote") <= 10
    assert "VALOR-SECRETO" not in repr(log.events)
    assert [lvl for lvl, e, _ in log.events if e == "lote concluído"] == ["WARNING"]
    errors = [f for lvl, e, f in log.events if lvl == "ERROR"]
    assert errors and all("chunk" in f for f in errors)


def test_falha_de_decodificacao_nao_derruba_chunk_gravado():
    log = CaptureLogger()
    runner = BatchRunner(log)

    def decode(row):
        raise MappingError("falha")

    result = runner.run(table="t", operation="insert_many", rows=[{"a": 1}], send=lambda c: list(c),
                        decode=decode, batch_size=1, mode="continue")
    item = result.items[0]
    assert item.ok and item.entity is None and isinstance(item.error, MappingError)


def test_linhas_devolvidas_em_numero_diferente_nao_casam_com_itens():
    runner = BatchRunner(CaptureLogger())
    result = runner.run(table="t", operation="upsert_many", rows=[{"a": 1}, {"a": 2}],
                        send=lambda c: [{"a": 1}], decode=lambda r: r, batch_size=2, mode="continue")
    assert result.all_ok and [o.entity for o in result.items] == [None, None]


def test_lote_pequeno_nao_emite_progresso():
    repo, _, _, log = build_repository(D)
    repo.insert_many(rows(3), BatchOptions(batch_size=3))
    assert "progresso do lote" not in [e for _, e, _ in log.events]
