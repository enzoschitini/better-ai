"""Smoke LIVE contra o projeto de teste. Pulado sem SBX_TEST_ALLOW_LIVE=1."""
from __future__ import annotations

import pytest

from src.database.supabase_integration import BytesSource, Condition, Op, Query, UploadOptions
from src.database.supabase_integration.contracts import CompositeStatus
from src.database.supabase_integration.errors import RecordNotFoundError

pytestmark = pytest.mark.integration


def test_tabela_crud_roundtrip(live, run_id):
    repo = live.tables.table("sbx_test_items")
    created = repo.insert({"name": f"{run_id}-a", "qty": 1})
    try:
        assert repo.get_by_id(created["id"])["name"] == f"{run_id}-a"
        assert repo.update(created["id"], {"qty": 5})["qty"] == 5
        found = repo.find(Query.where(Condition("name", Op.EQ, f"{run_id}-a")))
        assert [r["id"] for r in found] == [created["id"]]
    finally:
        repo.delete(created["id"])
    assert repo.delete(created["id"]).removed is False  # idempotente
    with pytest.raises(RecordNotFoundError):
        repo.get_by_id(created["id"])


def test_arquivo_upload_download_url_delete(live, run_id):
    data = b"conteudo de teste " + run_id.encode()
    stored = live.storage.upload(
        BytesSource(data, filename=f"{run_id}.txt", content_type="text/plain"), UploadOptions(folder=run_id)
    )
    try:
        assert live.storage.exists(stored.path)
        assert live.storage.download(stored.path) == data
        assert live.storage.signed_url(stored.path, ttl_seconds=60).startswith("http")
    finally:
        report = live.storage.delete([stored.path])
    assert stored.path in report.removed
    assert not live.storage.exists(stored.path)


@pytest.mark.e2e
def test_fachada_arquivo_mais_registro(live, run_id):
    r = live.save_file_with_record(
        "sbx_test_items",
        BytesSource(b"e2e " + run_id.encode(), filename=f"{run_id}.txt", content_type="text/plain"),
        lambda s: {"name": f"{run_id}-e2e", "bucket": s.bucket, "path": s.path},
        UploadOptions(folder=run_id),
    )
    assert r.status is CompositeStatus.COMPLETA
    d = live.delete_record_and_file("sbx_test_items", r.record["id"], (r.stored_file.bucket, r.stored_file.path))
    assert d.status is CompositeStatus.COMPLETA
