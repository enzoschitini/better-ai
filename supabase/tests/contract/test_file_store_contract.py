"""Bateria de contrato do ``FileStore`` (research/07 §15), parametrizável por fábrica.

Hoje roda contra ``SupabaseStorage`` + ``InMemoryStorageTransport``. Para rodar contra o adapter
real (T-306), registre outra fábrica em ``FACTORIES`` (mesma assinatura: ``StorageSettings -> FileStore``)
com o marcador ``integration``. A bateria usa SÓ a API pública de ``FileStore``.
"""
import io

import pytest

from bai_supabase.contracts.settings import StorageSettings
from bai_supabase.contracts.storage import (
    BytesSource,
    CollisionPolicy,
    FileStore,
    StreamSource,
    UploadOptions,
)
from bai_supabase.errors.exceptions import (
    FileAlreadyExistsError,
    FileNotFoundInStorageError,
    FileTooLargeError,
    SupabaseIntegrationError,
    ValidationError,
)
from bai_supabase.storage import SupabaseStorage
from tests.fakes.executor import PassThroughExecutor
from tests.fakes.logger import CaptureLogger
from tests.fakes.storage_transport import InMemoryStorageTransport

PNG = b"\x89PNG\r\n\x1a\n" + b"\x07" * 200


def fake_store(settings: StorageSettings) -> FileStore:
    return SupabaseStorage(
        transport=InMemoryStorageTransport(), executor=PassThroughExecutor(), logger=CaptureLogger(), settings=settings
    )


FACTORIES = {"fake": fake_store}


@pytest.fixture(params=sorted(FACTORIES))
def make_store(request):
    base = dict(default_bucket="media", buckets_public=("pub",), buckets_allowlist=("media", "pub"))

    def _make(**overrides) -> FileStore:
        return FACTORIES[request.param](StorageSettings(**{**base, **overrides}))

    return _make


@pytest.fixture
def store(make_store) -> FileStore:
    return make_store(max_file_bytes=1_000_000, list_page_size=3)


def test_roundtrip_upload_download_metadata(store, tmp_path):
    out = store.upload(BytesSource(PNG, filename="Foto Ç.png"), UploadOptions(folder="fotos", metadata={"origem": "teste"}))
    assert (out.bucket, out.size, out.content_type, out.original_name) == ("media", len(PNG), "image/png", "Foto Ç.png")
    assert out.metadata["origem"] == "teste"
    assert store.download(out.path) == PNG
    assert store.download_to(out.path, tmp_path / "x.png").read_bytes() == PNG
    assert store.exists(out.path) and not store.exists("fotos/inexistente.png")


def test_paths_are_unique_for_same_name(store):
    a = store.upload(BytesSource(PNG, filename="a.png"))
    b = store.upload(BytesSource(PNG, filename="a.png"))
    assert a.path != b.path


def test_collision_policies(store):
    opts = dict(path="k/a.png")
    store.upload(BytesSource(PNG, filename="a.png"), UploadOptions(**opts))
    with pytest.raises(FileAlreadyExistsError):
        store.upload(BytesSource(PNG, filename="a.png"), UploadOptions(**opts))
    versioned = store.upload(BytesSource(PNG, filename="a.png"), UploadOptions(**opts, collision=CollisionPolicy.VERSION))
    assert versioned.path != "k/a.png" and store.exists("k/a.png") and store.exists(versioned.path)
    new = PNG + b"novo"
    store.upload(BytesSource(new, filename="a.png"), UploadOptions(**opts, collision=CollisionPolicy.OVERWRITE))
    assert store.download("k/a.png") == new


def test_validation_before_transfer(store, make_store):
    with pytest.raises(ValidationError):
        store.upload(BytesSource(PNG, filename="a.png"), UploadOptions(path="../x/a.png"))
    with pytest.raises(ValidationError):
        store.upload(BytesSource(PNG, filename="a.png"), UploadOptions(bucket="outro"))
    with pytest.raises(ValidationError):
        store.upload(BytesSource(b"MZ\x90\x00" * 20, filename="musica.mp3"))
    with pytest.raises(FileTooLargeError):
        store.upload(StreamSource(io.BytesIO(b"x" * 10), size=2_000_000, filename="a.bin"))
    tiny = make_store(max_file_bytes=10)
    with pytest.raises(FileTooLargeError):
        tiny.upload(BytesSource(PNG, filename="a.png"))
    with pytest.raises(ValidationError):
        store.upload(BytesSource(b"", filename="a.png"))


@pytest.mark.parametrize("bad", ["../x", "/abs", "a\\b", "a/%2e%2e/b", "a\x00b", "con"])
def test_path_traversal_rejected_in_download_exists_delete_signed(store, bad):
    for call in (store.download, store.exists, store.signed_url, lambda p: store.delete([p])):
        with pytest.raises(ValidationError):
            call(bad)


def test_missing_object_raises_domain_error(store):
    with pytest.raises(FileNotFoundInStorageError):
        store.download("nao/existe.png")


def test_signed_url_ttl_rules(store):
    assert store.signed_url("a/b.png")
    assert store.signed_url("a/b.png", ttl_seconds=3600)
    for bad in (0, -1, 3601):
        with pytest.raises(ValidationError):
            store.signed_url("a/b.png", ttl_seconds=bad)


def test_public_url_only_for_public_buckets(store):
    assert store.public_url("logo.png", bucket="pub")
    with pytest.raises(ValidationError):
        store.public_url("logo.png", bucket="media")


def test_list_pagination_covers_everything_without_duplicates(store):
    names = [store.upload(BytesSource(f"conteudo {i}".encode(), filename=f"n{i}.txt"), UploadOptions(path=f"lista/n{i:02d}.txt")).path for i in range(7)]
    seen, offset = [], 0
    while True:
        page = store.list("lista", offset=offset)
        assert len(page.items) <= page.limit == 3
        seen += [i.path for i in page.items]
        if not page.has_more:
            break
        offset += page.limit
    assert seen == names


def test_delete_idempotent_batch_and_prefix(store):
    for i in range(5):
        store.upload(BytesSource(b"x", filename="a.txt"), UploadOptions(path=f"d/{i}.txt"))
    first = store.delete(["d/0.txt", "d/1.txt", "d/nao-existe.txt"])
    assert sorted(first.removed) == ["d/0.txt", "d/1.txt"] and first.failed == {}
    again = store.delete(["d/0.txt"])
    assert again.failed == {} and again.removed == []
    report = store.delete_prefix("d")
    assert sorted(report.removed) == ["d/2.txt", "d/3.txt", "d/4.txt"] and report.failed == {}
    assert store.list("d").items == []
    with pytest.raises(ValidationError):
        store.delete_prefix("")


def test_only_domain_errors_escape(store):
    for call in (lambda: store.download("a/nao.png"), lambda: store.upload(BytesSource(b"", filename="a")),
                 lambda: store.signed_url("a", ttl_seconds=0)):
        with pytest.raises(SupabaseIntegrationError):
            call()
