"""SupabaseStorageTransport contra um cliente SDK FALSO e httpx.MockTransport (sem rede)."""
import io
import json
from pathlib import Path

import httpx
import pytest
from storage3.exceptions import StorageApiError

from bai_supabase.adapters.storage_transport import SupabaseStorageTransport
from bai_supabase.contracts.transports import StorageTransport
from bai_supabase.errors.exceptions import (
    ConfigurationError,
    FileAlreadyExistsError,
    FileNotFoundInStorageError,
    ServiceUnavailableError,
    SupabaseIntegrationError,
)
from bai_supabase.storage.service import SizedStorageTransport

SIGNED = "https://proj.supabase.test/storage/v1/object/sign/media/a/b.bin?token=SECRET-SIGNED-TOKEN"


class FakeBucket:
    def __init__(self, owner, name):
        self.owner, self.name = owner, name

    def _call(self, method, *args):
        self.owner.calls.append((method, self.name, *args))
        err = self.owner.errors.pop(method, None)
        if err:
            raise err
        return self.owner.results.get(method)

    def upload(self, path, file, file_options=None):
        self.owner.uploaded = {"path": path, "file": file, "options": dict(file_options or {})}
        return self._call("upload", path)

    def download(self, path, *a, **k):
        return self._call("download", path)

    def create_signed_url(self, path, expires_in, options=None):
        self._call("create_signed_url", path, expires_in)
        return {"signedURL": SIGNED, "signedUrl": SIGNED}

    def get_public_url(self, path, options=None):
        return f"https://proj.supabase.test/storage/v1/object/public/{self.name}/{path}"

    def exists(self, path):
        return self._call("exists", path)

    def info(self, path):
        return self._call("info", path)

    def list(self, path=None, options=None):
        self.owner.list_args = (path, options)
        return self._call("list", path)

    def remove(self, paths):
        return self._call("remove", paths)


class FakeClient:
    def __init__(self):
        self.calls, self.errors, self.results = [], {}, {}
        self.uploaded = None
        self.list_args = None
        self.storage = self

    def from_(self, name):
        return FakeBucket(self, name)


class RecordingResumable:
    def __init__(self):
        self.args = None

    def upload(self, *args, **kwargs):
        self.args = (args, kwargs)


def make(handler=None, resumable=None):
    client = FakeClient()
    http = httpx.Client(transport=httpx.MockTransport(handler or (lambda r: httpx.Response(200, content=b"")))) if handler else None
    return SupabaseStorageTransport(lambda: client, resumable=resumable, http_client=http), client


def test_implements_contracts():
    t, _ = make()
    assert isinstance(t, StorageTransport) and isinstance(t, SizedStorageTransport)


def test_upload_standard_bytes_options_mapping():
    t, c = make()
    t.upload_standard("media", "a/b.png", b"abc", content_type="image/png", upsert=True,
                      cache_control_seconds=60, metadata={"original_name": "x.png"})
    assert c.uploaded["path"] == "a/b.png" and c.uploaded["file"] == b"abc"
    assert c.uploaded["options"] == {"content-type": "image/png", "upsert": "true", "cache-control": "60",
                                     "metadata": {"original_name": "x.png"}}
    t.upload_standard("media", "a/c.png", b"abc")
    assert c.uploaded["options"] == {"content-type": "application/octet-stream"}  # sem upsert por padrão


def test_upload_standard_path_opens_and_closes_file(tmp_path):
    f = tmp_path / "x.bin"
    f.write_bytes(b"123")
    t, c = make()
    t.upload_standard("media", "x.bin", f)
    handle = c.uploaded["file"]
    assert hasattr(handle, "read") and handle.closed  # fechado pelo transporte


def test_upload_standard_buffered_reader_passed_through_and_other_streams_read():
    t, c = make()
    with open(__file__, "rb") as fh:
        t.upload_standard("media", "x", fh)
        assert c.uploaded["file"] is fh
    t.upload_standard("media", "y", io.BytesIO(b"zzz"))
    assert c.uploaded["file"] == b"zzz"


def test_sdk_exceptions_become_domain_errors_never_leak():
    t, c = make()
    c.errors["upload"] = StorageApiError("Duplicate", "Duplicate", 409)
    with pytest.raises(FileAlreadyExistsError) as ei:
        t.upload_standard("media", "a", b"x")
    assert isinstance(ei.value.__cause__, StorageApiError)  # causa preservada
    c.errors["download"] = StorageApiError("not found", "NoSuchKey", 404)
    with pytest.raises(FileNotFoundInStorageError):
        t.download_bytes("media", "a")
    c.errors["list"] = httpx.ConnectError("sem rede")
    with pytest.raises(ServiceUnavailableError):
        t.list_objects("media", "", 10, 0)
    c.errors["remove"] = RuntimeError("???")
    with pytest.raises(SupabaseIntegrationError):
        t.remove("media", ["a"])


def test_download_bytes_signed_public_exists_info():
    t, c = make()
    c.results.update(download=b"conteudo", exists=True, info={"size": 42})
    assert t.download_bytes("media", "a") == b"conteudo"
    assert t.create_signed_url("media", "a/b.bin", 300) == SIGNED
    assert ("create_signed_url", "media", "a/b.bin", 300) in c.calls
    assert t.public_url("media", "a.png").endswith("/public/media/a.png")
    assert t.exists("media", "a") is True
    assert t.object_size("media", "a") == 42
    c.results["info"] = {"metadata": {"size": 7}}
    assert t.object_size("media", "a") == 7
    c.results["info"] = {}
    assert t.object_size("media", "a") is None


def test_list_objects_maps_files_and_folders_and_sends_options():
    t, c = make()
    c.results["list"] = [
        {"name": "sub", "id": None, "updated_at": None, "metadata": None},
        {"name": "a.png", "id": "uuid-1", "updated_at": "2026-01-01", "metadata": {"size": 10, "mimetype": "image/png"}},
    ]
    rows = t.list_objects("media", "docs/", 5, 10, sort_by="updated_at")
    assert c.list_args == ("docs/", {"limit": 5, "offset": 10, "sortBy": {"column": "updated_at", "order": "asc"}})
    assert (rows[0].is_folder, rows[0].path, rows[0].name) == (True, "docs/sub", "sub")
    assert (rows[1].is_folder, rows[1].path, rows[1].size, rows[1].content_type) == (False, "docs/a.png", 10, "image/png")
    assert t.list_objects("media", "", 5, 0)[0].path == "sub"


def test_remove_returns_names_actually_removed():
    t, c = make()
    c.results["remove"] = [{"name": "a/b.png"}, {"name": "a/c.png"}]
    assert t.remove("media", ["a/b.png", "a/c.png", "a/zzz.png"]) == ["a/b.png", "a/c.png"]
    c.results["remove"] = []
    assert t.remove("media", ["x"]) == []


def test_resumable_delegates_and_requires_configuration():
    rec = RecordingResumable()
    t, _ = make(resumable=rec)
    t.upload_resumable("media", "big.bin", io.BytesIO(b"x"), 1, content_type="video/mp4", upsert=True,
                       cache_control_seconds=10, metadata={"k": "v"}, chunk_bytes=123)
    args, kwargs = rec.args
    assert args[:2] == ("media", "big.bin") and args[3] == 1
    assert kwargs == {"content_type": "video/mp4", "upsert": True, "cache_control_seconds": 10,
                      "metadata": {"k": "v"}, "chunk_bytes": 123}
    plain, _ = make()
    with pytest.raises(ConfigurationError):
        plain.upload_resumable("media", "big.bin", io.BytesIO(b"x"), 1)


def test_download_to_file_streams_in_blocks_atomically(tmp_path):
    body = b"0123456789" * 300_000  # 3 MB: vários blocos de 1 MiB
    seen = []

    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(200, content=body)

    t, c = make(handler)
    dest = tmp_path / "out" / "video.bin"
    dest.parent.mkdir()
    assert t.download_to_file("media", "a/b.bin", dest) == dest
    assert dest.read_bytes() == body
    assert not list(dest.parent.glob("*.part"))
    assert seen == [SIGNED]


def test_download_to_file_failure_leaves_no_partial_file_and_maps_error(tmp_path):
    class Boom(httpx.SyncByteStream):
        def __iter__(self):
            yield b"parcial"
            raise httpx.ReadError("queda no meio")

    t, _ = make(lambda r: httpx.Response(200, stream=Boom()))
    dest = tmp_path / "v.bin"
    with pytest.raises(ServiceUnavailableError):
        t.download_to_file("media", "a/b.bin", dest)
    assert not dest.exists() and not list(tmp_path.glob("*.part"))


def test_download_to_file_http_error_maps_and_keeps_existing_destination(tmp_path):
    dest = tmp_path / "v.bin"
    dest.write_bytes(b"antigo")
    t, _ = make(lambda r: httpx.Response(404, content=json.dumps({"message": "x", "error": "not_found", "statusCode": "404"})))
    with pytest.raises(FileNotFoundInStorageError) as ei:
        t.download_to_file("media", "a/b.bin", dest)
    assert "SECRET-SIGNED-TOKEN" not in str(ei.value) and "SECRET-SIGNED-TOKEN" not in repr(ei.value.to_dict())
    assert dest.read_bytes() == b"antigo"
