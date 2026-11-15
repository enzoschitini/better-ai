"""Fachada: delegação e operações combinadas (research/08, decisão C-1)."""
from __future__ import annotations

import pytest

from bai_supabase.config.settings import SupabaseSettings
from bai_supabase.contracts import (
    BytesSource,
    CompositeStatus,
    ConnectionSettings,
    Secret,
    StorageSettings,
    TableDescriptor,
    TablesSettings,
)
from bai_supabase.errors import (
    DuplicateRecordError,
    RecordNotFoundError,
    ServiceUnavailableError,
)
from bai_supabase.factories import create_integration
from tests.fakes.logger import CaptureLogger
from tests.fakes.storage_transport import InMemoryStorageTransport
from tests.fakes.table_transport import InMemoryTableTransport

BUCKET = "docs"


@pytest.fixture
def env():
    tt = InMemoryTableTransport()
    tt.configure("documentos")
    st = InMemoryStorageTransport()
    log = CaptureLogger()
    settings = SupabaseSettings(
        connection=ConnectionSettings(url="https://x.supabase.co", secret_key=Secret("segredo-plantado-123"), retry_max_attempts=1),
        tables=TablesSettings(allowlist=("documentos",)),
        storage=StorageSettings(default_bucket=BUCKET, buckets_allowlist=(BUCKET,)),
    )
    sb = create_integration(
        settings,
        descriptors=[TableDescriptor("documentos")],
        logger=log,
        table_transport=tt,
        storage_transport=st,
    )
    return sb, tt, st, log


def _src(name="a.txt"):
    return BytesSource(b"conteudo", filename=name, content_type="text/plain")


def _factory(stored):
    return {"titulo": "doc", "bucket": stored.bucket, "path": stored.path}


def test_save_file_with_record_completa(env):
    sb, tt, st, _ = env
    r = sb.save_file_with_record("documentos", _src(), _factory)
    assert r.status is CompositeStatus.COMPLETA
    assert r.steps_done == ["arquivo_gravado", "registro_gravado"]
    assert not r.orphan_possible
    assert (BUCKET, r.stored_file.path) in st.objects
    assert tt.rows("documentos")[0]["path"] == r.stored_file.path


def test_insert_falha_compensa_apagando_arquivo(env):
    sb, tt, st, _ = env
    err = DuplicateRecordError("duplicado")
    tt.fail_when("insert", lambda rows: True, err)
    r = sb.save_file_with_record("documentos", _src(), _factory)
    assert r.status is CompositeStatus.FALHOU
    assert r.error is err  # mesmo objeto, sem reembrulhar
    assert not r.orphan_possible
    assert st.objects == {}  # compensou


def test_insert_falha_e_compensacao_falha_vira_parcial_com_orfao_e_log(env):
    sb, tt, st, log = env
    tt.fail_when("insert", lambda rows: True, DuplicateRecordError("duplicado"))
    st.fail_next("remove", ServiceUnavailableError("fora"), times=5)
    r = sb.save_file_with_record("documentos", _src(), _factory)
    assert r.status is CompositeStatus.PARCIAL
    assert r.orphan_possible
    assert r.stored_file is not None
    orphan_events = [e for e in log.events if e[1] == "composite.orfao_possivel"]
    assert len(orphan_events) == 1 and orphan_events[0][0] == "ERROR"
    assert orphan_events[0][2]["orfao_possivel"] is True
    assert isinstance(r.error, DuplicateRecordError)  # erro original, sem segundo erro


def test_raise_if_failed_levanta_o_mesmo_objeto(env):
    sb, tt, _, _ = env
    err = DuplicateRecordError("dup")
    tt.fail_when("insert", lambda rows: True, err)
    r = sb.save_file_with_record("documentos", _src(), _factory)
    with pytest.raises(DuplicateRecordError) as ei:
        r.raise_if_failed()
    assert ei.value is err


def test_replace_usa_caminho_novo_e_apaga_antigo_por_ultimo(env):
    sb, tt, st, _ = env
    first = sb.save_file_with_record("documentos", _src(), _factory)
    rec_id = first.record["id"]
    old = (first.stored_file.bucket, first.stored_file.path)
    r = sb.replace_file_in_record(
        "documentos", rec_id, _src("b.txt"), lambda s: {"bucket": s.bucket, "path": s.path}, old_ref=old
    )
    assert r.status is CompositeStatus.COMPLETA
    assert r.stored_file.path != old[1]
    assert (BUCKET, old[1]) not in st.objects
    assert (BUCKET, r.stored_file.path) in st.objects
    assert r.steps_done[-1] == "arquivo_antigo_apagado"


def test_replace_update_falha_nao_mexe_no_arquivo_antigo(env):
    sb, tt, st, _ = env
    first = sb.save_file_with_record("documentos", _src(), _factory)
    old = (first.stored_file.bucket, first.stored_file.path)
    r = sb.replace_file_in_record(
        "documentos", "id-inexistente", _src("b.txt"), lambda s: {"path": s.path}, old_ref=old
    )
    assert r.status is CompositeStatus.FALHOU
    assert isinstance(r.error, RecordNotFoundError)
    assert old in st.objects  # antigo intacto
    assert len(st.objects) == 1  # novo foi compensado


def test_replace_apagar_antigo_falha_vira_parcial(env):
    sb, tt, st, _ = env
    first = sb.save_file_with_record("documentos", _src(), _factory)
    old = (first.stored_file.bucket, first.stored_file.path)
    st.fail_next("remove", ServiceUnavailableError("fora"), times=5)
    r = sb.replace_file_in_record(
        "documentos", first.record["id"], _src("b.txt"), lambda s: {"path": s.path}, old_ref=old
    )
    assert r.status is CompositeStatus.PARCIAL and r.orphan_possible
    assert r.record is not None  # registro já aponta para o novo


def test_delete_record_and_file_ordem_registro_primeiro(env):
    sb, tt, st, _ = env
    first = sb.save_file_with_record("documentos", _src(), _factory)
    ref = (first.stored_file.bucket, first.stored_file.path)
    r = sb.delete_record_and_file("documentos", first.record["id"], ref)
    assert r.status is CompositeStatus.COMPLETA
    assert r.steps_done == ["registro_apagado", "arquivo_apagado"]
    assert tt.rows("documentos") == [] and st.objects == {}


def test_delete_arquivo_falha_vira_parcial_registro_ja_apagado(env):
    sb, tt, st, _ = env
    first = sb.save_file_with_record("documentos", _src(), _factory)
    ref = (first.stored_file.bucket, first.stored_file.path)
    st.fail_next("remove", ServiceUnavailableError("fora"), times=5)
    r = sb.delete_record_and_file("documentos", first.record["id"], ref)
    assert r.status is CompositeStatus.PARCIAL and r.orphan_possible
    assert tt.rows("documentos") == []


def test_segredo_plantado_nao_aparece_nos_logs(env):
    sb, tt, st, log = env
    tt.fail_when("insert", lambda rows: True, DuplicateRecordError("duplicado"))
    sb.save_file_with_record("documentos", _src(), _factory)
    assert "segredo-plantado-123" not in repr(log.events)


def test_fachada_expoe_tables_e_storage_sem_logica_propria(env):
    sb, *_ = env
    repo = sb.tables.table("documentos")
    created = repo.insert({"titulo": "x"})
    assert repo.get_by_id(created["id"])["titulo"] == "x"
