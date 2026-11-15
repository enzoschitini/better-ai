"""SupabaseStorage com transporte, executor e logger falsos (sem rede)."""
import io
import threading
import time

import pytest

from src.database.supabase_integration.contracts.resilience import Operation
from src.database.supabase_integration.contracts.settings import StorageSettings
from src.database.supabase_integration.contracts.storage import (
    BytesSource,
    CollisionPolicy,
    FileStore,
    PathSource,
    StreamSource,
    UploadOptions,
)
from src.database.supabase_integration.errors.exceptions import (
    ConfigurationError,
    FileAlreadyExistsError,
    FileNotFoundInStorageError,
    FileTooLargeError,
    OperationTimeoutError,
    PermissionDeniedError,
    ServiceUnavailableError,
    ValidationError,
)
from src.database.supabase_integration.storage import PreservedNameNaming, SupabaseStorage
from src.database.supabase_integration.tests.fakes.executor import PassThroughExecutor
from src.database.supabase_integration.tests.fakes.logger import CaptureLogger
from src.database.supabase_integration.tests.fakes.storage_transport import InMemoryStorageTransport

MiB = 1024 * 1024
PNG = b"\x89PNG\r\n\x1a\n" + b"\x01" * 100


def make(transport=None, executor=None, **overrides):
    base = dict(default_bucket="media", buckets_public=("pub",), buckets_allowlist=("media", "pub"))
    base.update(overrides)
    t = transport or InMemoryStorageTransport()
    ex = executor or PassThroughExecutor()
    lg = CaptureLogger()
    return SupabaseStorage(transport=t, executor=ex, logger=lg, settings=StorageSettings(**base)), t, ex, lg


def test_implements_file_store_contract():
    store, *_ = make()
    assert isinstance(store, FileStore)


# --- upload -------------------------------------------------------------------------
def test_upload_bytes_standard_mode_generates_dated_uuid_path_and_metadata():
    store, t, ex, _ = make()
    out = store.upload(BytesSource(PNG, filename="Minha Foto.PNG"), UploadOptions(folder="fotos", metadata={"owner": "u1"}))
    assert out.bucket == "media" and out.size == len(PNG) and out.content_type == "image/png"
    assert out.upload_mode == "standard" and out.original_name == "Minha Foto.PNG"
    assert out.path.startswith("fotos/") and out.path.endswith(".png") and "minha" not in out.path
    assert out.metadata == {"owner": "u1", "original_name": "Minha Foto.PNG"}
    stored = t.objects[("media", out.path)]
    assert stored.data == PNG and stored.metadata == out.metadata and stored.cache_control_seconds == 3600


def test_upload_declares_operation_to_executor():
    store, t, ex, _ = make()
    store.upload(BytesSource(PNG, filename="a.png"))
    op = ex.operations[-1]
    assert (op.name, op.category, op.idempotent, op.restartable) == ("storage.upload", "file_transfer", False, True)
    store.upload(BytesSource(PNG, filename="a.png"), UploadOptions(path="x/a.png", collision=CollisionPolicy.OVERWRITE))
    assert ex.operations[-1].idempotent is True


def test_non_restartable_stream_declared_to_executor():
    store, t, ex, _ = make()
    store.upload(StreamSource(io.BytesIO(PNG), size=len(PNG), filename="a.png", restartable=False))
    assert ex.operations[-1].restartable is False
    store.upload(StreamSource(io.BytesIO(PNG), size=len(PNG), filename="b.png", restartable=True))
    assert ex.operations[-1].restartable is True


def test_validation_happens_before_any_network_call():
    store, t, *_ = make(max_file_bytes=100)
    cases = [
        (BytesSource(PNG, filename="a.png"), UploadOptions(bucket="intruso"), ValidationError),  # bucket fora da allowlist
        (BytesSource(PNG, filename="a.png"), None, FileTooLargeError),  # tamanho
        (BytesSource(b"", filename="a.png"), None, ValidationError),  # vazio
        (BytesSource(b"MZ\x90\x00" + b"\x00" * 20, filename="musica.mp3"), None, ValidationError),  # divergência
        (BytesSource(b"x" * 10, filename="a.txt"), UploadOptions(path="../fora.txt"), ValidationError),  # traversal
        (BytesSource(b"x" * 10, filename="a.txt"), UploadOptions(metadata={"k": 1}), ValidationError),
    ]
    for source, opts, error in cases:
        with pytest.raises(error):
            store.upload(source, opts)
    assert t.calls == []


def test_bucket_default_missing_is_configuration_error():
    store, t, *_ = make(default_bucket=None, buckets_allowlist=())
    with pytest.raises(ConfigurationError):
        store.upload(BytesSource(PNG, filename="a.png"))
    assert t.calls == []


def test_allowed_mime_and_public_bucket_dangerous_types():
    store, t, *_ = make(allowed_mime=("image/*", "text/*"))
    with pytest.raises(ValidationError):
        store.upload(BytesSource(b"%PDF-1.4 " + b"x" * 50, filename="a.pdf"))
    with pytest.raises(ValidationError):
        store.upload(BytesSource(b"<html></html>", filename="a.html"), UploadOptions(bucket="pub"))
    assert t.calls == []


def test_explicit_path_is_used_after_validation():
    store, t, *_ = make()
    out = store.upload(BytesSource(PNG, filename="a.png"), UploadOptions(path="avatar/u1.png"))
    assert out.path == "avatar/u1.png"


def test_custom_naming_strategy_injected():
    t = InMemoryStorageTransport()
    store = SupabaseStorage(
        transport=t, executor=PassThroughExecutor(), logger=CaptureLogger(),
        settings=StorageSettings(default_bucket="media"), naming=PreservedNameNaming(),
    )
    out = store.upload(BytesSource(PNG, filename="Foto Bonita.png"), UploadOptions(folder="f"))
    assert out.path == "f/foto-bonita.png"


def test_collision_reject_default_overwrite_and_version():
    store, t, ex, lg = make()
    opts = UploadOptions(path="a/b.png")
    store.upload(BytesSource(PNG, filename="b.png"), opts)
    with pytest.raises(FileAlreadyExistsError):
        store.upload(BytesSource(PNG, filename="b.png"), opts)
    new = PNG + b"2"
    over = store.upload(BytesSource(new, filename="b.png"), UploadOptions(path="a/b.png", collision=CollisionPolicy.OVERWRITE))
    assert over.path == "a/b.png" and t.objects[("media", "a/b.png")].data == new
    assert any(level == "WARNING" and "sobrescrevendo" in ev for level, ev, _ in lg.events)
    v = store.upload(BytesSource(PNG, filename="b.png"), UploadOptions(path="a/b.png", collision=CollisionPolicy.VERSION))
    assert v.path == "a/b-v2.png"
    assert t.objects[("media", "a/b.png")].data == new  # o antigo foi preservado
    v3 = store.upload(BytesSource(PNG, filename="b.png"), UploadOptions(path="a/b.png", collision=CollisionPolicy.VERSION))
    assert v3.path == "a/b-v3.png"


def test_version_recovers_from_race_on_server():
    store, t, *_ = make()
    store.upload(BytesSource(PNG, filename="b.png"), UploadOptions(path="a/b.png"))
    # corrida: alguém grava a-v2 entre o "existe?" e o upload
    real_exists = t.exists

    def racy_exists(bucket, path):
        found = real_exists(bucket, path)
        if path == "a/b-v2.png" and not found:
            t.put(bucket, path, b"intruso")
        return found

    t.exists = racy_exists  # type: ignore[method-assign]
    v = store.upload(BytesSource(PNG, filename="b.png"), UploadOptions(path="a/b.png", collision=CollisionPolicy.VERSION))
    assert v.path == "a/b-v3.png"


def test_mode_chosen_by_size_standard_vs_resumable():
    store, t, *_ = make(resumable_threshold_bytes=1000, resumable_chunk_bytes=400, memory_cap_bytes=10 * MiB)
    small = store.upload(BytesSource(b"a" * 1000, filename="a.bin"))
    big = store.upload(BytesSource(b"a" * 1001, filename="b.bin"))
    assert (small.upload_mode, big.upload_mode) == ("standard", "resumable")
    assert t.called("upload_standard") == 1 and t.called("upload_resumable") == 1
    assert t.chunks_read == [400, 400, 201]
    assert t.objects[("media", big.path)].data == b"a" * 1001


class SyntheticStream:
    """Gera bytes sob demanda (nunca guarda o arquivo): simula um arquivo gigante."""

    def __init__(self, total: int, head: bytes = b"") -> None:
        self.total, self.pos, self.head = total, 0, head
        self.max_read = 0

    def read(self, n: int = -1) -> bytes:
        if n is None or n < 0:
            raise AssertionError("read() sem tamanho num arquivo grande")
        n = min(n, self.total - self.pos)
        self.max_read = max(self.max_read, n)
        out = (self.head + b"\x00" * n)[:n] if self.pos == 0 else b"\x00" * n
        self.pos += n
        return out

    def seekable(self) -> bool:
        return False


def test_simulated_large_file_stream_never_allocated_at_once():
    total = 300 * MiB
    t = InMemoryStorageTransport(keep_data=False)
    store, t, *_ = make(transport=t, max_file_bytes=1024 * MiB, resumable_chunk_bytes=6 * MiB)
    stream = SyntheticStream(total)
    out = store.upload(StreamSource(stream, size=total, filename="aula.bin", content_type="application/octet-stream"))
    assert out.upload_mode == "resumable" and out.size == total
    assert t.objects[("media", out.path)].length == total
    assert t.max_chunk_seen <= 6 * MiB and stream.max_read <= 6 * MiB
    assert sum(t.chunks_read) == total  # blocos curtos (cabeçalho devolvido ao stream) são normais


def test_large_stream_without_known_size_is_aborted_over_limit_without_upload():
    store, t, *_ = make(max_file_bytes=5 * MiB)
    with pytest.raises(FileTooLargeError):
        store.upload(StreamSource(SyntheticStream(50 * MiB), filename="x.bin"))
    assert t.calls == []


def test_path_source_upload_resumable_reads_from_disk(tmp_path):
    f = tmp_path / "video.bin"
    f.write_bytes(b"\x00" * 3000)
    store, t, *_ = make(resumable_threshold_bytes=1000, resumable_chunk_bytes=1000)
    out = store.upload(PathSource(f))
    assert out.upload_mode == "resumable" and out.original_name == "video.bin"
    assert t.chunks_read == [1000, 1000, 1000]


def test_upload_failure_marks_outcome_unknown_and_keeps_identity():
    store, t, *_ = make()
    err = OperationTimeoutError("timeout")
    t.fail_next("upload_standard", err)
    with pytest.raises(OperationTimeoutError) as ei:
        store.upload(BytesSource(PNG, filename="a.png"))
    assert ei.value is err and err.outcome_unknown is True
    t.fail_next("upload_standard", ServiceUnavailableError("503"))
    with pytest.raises(ServiceUnavailableError) as ei2:
        store.upload(BytesSource(PNG, filename="a.png"))
    assert ei2.value.outcome_unknown
    t.fail_next("upload_standard", PermissionDeniedError("403"))
    with pytest.raises(PermissionDeniedError) as ei3:
        store.upload(BytesSource(PNG, filename="a.png"))
    assert not ei3.value.outcome_unknown


# --- download / URLs ------------------------------------------------------------------
def test_download_and_download_to(tmp_path):
    store, t, *_ = make()
    out = store.upload(BytesSource(PNG, filename="a.png"))
    assert store.download(out.path) == PNG
    dest = store.download_to(out.path, tmp_path / "sub" / "x.png")
    assert dest.read_bytes() == PNG and not list((tmp_path / "sub").glob("*.part"))
    assert [o.name for o in store._executor.operations if o.name == "storage.download"]  # noqa: SLF001
    with pytest.raises(FileNotFoundInStorageError):
        store.download("nao/existe.png")


def test_download_bytes_over_cap_refused_before_downloading():
    store, t, *_ = make(memory_cap_bytes=100)
    t.put("media", "grande.bin", b"x" * 500)
    with pytest.raises(ValidationError, match="download_to"):
        store.download("grande.bin")
    assert t.called("download_bytes") == 0


def test_download_rejects_traversal_and_unknown_bucket():
    store, t, *_ = make()
    for kwargs in ({"path": "../x"}, {"path": "a.png", "bucket": "outro"}):
        with pytest.raises(ValidationError):
            store.download(**kwargs)
    assert t.calls == []


def test_signed_url_ttl_default_ceiling_and_never_logged():
    store, t, ex, lg = make(signed_url_ttl_seconds=300, signed_url_max_ttl_seconds=3600)
    url = store.signed_url("a/b.png")
    assert "exp=300" in url and "FAKE-SIGNED-TOKEN" in url
    assert "exp=3600" in store.signed_url("a/b.png", ttl_seconds=3600)
    for bad in (3601, 0, -5, True):
        with pytest.raises(ValidationError):
            store.signed_url("a/b.png", ttl_seconds=bad)
    assert not any("FAKE-SIGNED-TOKEN" in repr(f) or "exp=" in repr(f) for _, _, f in lg.events)
    assert ex.operations[0].idempotent


def test_public_url_only_for_public_buckets():
    store, *_ = make()
    assert store.public_url("logo.png", bucket="pub").endswith("/public/pub/logo.png")
    with pytest.raises(ValidationError):
        store.public_url("logo.png")  # media é privado


def test_exists():
    store, t, *_ = make()
    out = store.upload(BytesSource(PNG, filename="a.png"))
    assert store.exists(out.path) is True and store.exists("nada.png") is False


# --- list ----------------------------------------------------------------------------
def _seed(t, n, folder="docs"):
    for i in range(n):
        t.put("media", f"{folder}/f{i:03d}.txt", b"x" * (i + 1), "text/plain")


def test_list_paginates_without_duplicates_or_gaps():
    store, t, *_ = make(list_page_size=4)
    _seed(t, 10)
    seen, offset = [], 0
    while True:
        page = store.list("docs", offset=offset)
        assert page.limit == 4 and page.offset == offset
        seen += [i.name for i in page.items]
        if not page.has_more:
            break
        offset += page.limit
    assert seen == [f"f{i:03d}.txt" for i in range(10)]


def test_list_exact_multiple_has_no_phantom_page_and_shows_folders():
    store, t, *_ = make()
    _seed(t, 4)
    t.put("media", "docs/sub/x.txt", b"1")
    page = store.list("docs/", limit=5)
    assert len(page.items) == 5 and not page.has_more
    assert [i.name for i in page.items if i.is_folder] == ["sub"]
    assert store.list("docs", limit=4).has_more


def test_list_validates_arguments():
    store, t, *_ = make()
    for kwargs in ({"limit": 0}, {"limit": 1001}, {"offset": -1}, {"prefix": "../x"}):
        with pytest.raises(ValidationError):
            store.list(**kwargs)
    assert t.calls == []


# --- delete --------------------------------------------------------------------------
def test_delete_is_idempotent_batches_and_reports():
    store, t, *_ = make(delete_batch_size=2)
    for n in "abcde":
        t.put("media", f"d/{n}.txt", b"1")
    rep = store.delete([f"d/{n}.txt" for n in "abcde"] + ["d/inexistente.txt", "d/a.txt"])
    assert rep.requested == 6 and sorted(rep.removed) == [f"d/{n}.txt" for n in "abcde"] and rep.failed == {}
    assert t.called("remove") == 3
    again = store.delete(["d/a.txt"])
    assert again.removed == [] and again.failed == {}  # inexistente = sucesso, sem erro


def test_delete_failed_batch_does_not_abort_the_others():
    store, t, ex, lg = make(delete_batch_size=1)
    for n in "abc":
        t.put("media", f"{n}.txt", b"1")
    t.fail_next("remove", PermissionDeniedError("negado"))
    rep = store.delete(["a.txt", "b.txt", "c.txt"])
    assert sorted(rep.removed) == ["b.txt", "c.txt"]
    assert list(rep.failed) == ["a.txt"] and "PermissionDeniedError" in rep.failed["a.txt"]
    assert any(level == "ERROR" for level, *_ in lg.events)


def test_delete_validates_everything_before_network():
    store, t, *_ = make()
    for bad in ([], "a.txt", ["ok.txt", "../fora.txt"]):
        with pytest.raises(ValidationError):
            store.delete(bad)
    assert t.calls == []


def test_delete_prefix_recursive_paginated_and_requires_prefix():
    store, t, *_ = make(list_page_size=3, delete_batch_size=2)
    for i in range(7):
        t.put("media", f"v/2026/10/f{i}.mp4", b"1")
    t.put("media", "v/2026/10/sub/deep.mp4", b"1")
    t.put("media", "v/2026/11/keep.mp4", b"1")
    rep = store.delete_prefix("v/2026/10/")
    assert rep.requested == 8 and len(rep.removed) == 8 and rep.failed == {}
    assert [k for k in t.objects] == [("media", "v/2026/11/keep.mp4")]
    for bad in ("", "/", "../x"):
        with pytest.raises(ValidationError):
            store.delete_prefix(bad)


# --- logs / concorrência --------------------------------------------------------------
def test_info_log_per_operation_without_content_or_secrets():
    store, t, ex, lg = make()
    out = store.upload(BytesSource(PNG, filename="segredo.png"))
    store.download(out.path)
    infos = [(ev, f) for level, ev, f in lg.events if level == "INFO"]
    assert [ev for ev, _ in infos] == ["storage.upload concluído", "storage.download concluído"]
    f = infos[0][1]
    assert f["bucket"] == "media" and f["path"] == out.path and f["size_bytes"] == len(PNG)
    assert f["mode"] == "standard" and "duration_ms" in f
    assert PNG.decode("latin1") not in repr(lg.events)


def test_failure_logged_once_at_the_boundary_with_expected_levels():
    store, t, ex, lg = make()
    with pytest.raises(ValidationError):
        store.download("../x")
    t.fail_next("download_bytes", PermissionDeniedError("negado"))
    t.put("media", "a.bin", b"1")
    with pytest.raises(PermissionDeniedError):
        store.download("a.bin")
    levels = lg.levels()
    assert levels.count("WARNING") == 1 and levels.count("ERROR") == 1


def test_concurrent_transfers_limited_by_semaphore():
    active, peak, lock = 0, 0, threading.Lock()

    class Slow(InMemoryStorageTransport):
        def download_bytes(self, bucket, path):
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
            time.sleep(0.05)
            with lock:
                active -= 1
            return b"x"

    slow = Slow()
    slow.put("media", "a.bin", b"x")
    store, t, *_ = make(transport=slow, max_concurrent_transfers=2)
    threads = [threading.Thread(target=store.download, args=("a.bin",)) for _ in range(6)]
    [th.start() for th in threads]
    [th.join() for th in threads]
    assert peak == 2


def test_invalid_concurrency_setting_fails_on_construction():
    with pytest.raises(ConfigurationError):
        make(max_concurrent_transfers=0)
