"""Cliente TUS mínimo contra um servidor TUS simulado (httpx.MockTransport, sem rede)."""
import base64
import io

import httpx
import pytest

from src.database.supabase_integration.adapters.tus import TusClient, build_upload_metadata
from src.database.supabase_integration.errors.exceptions import (
    FileAlreadyExistsError,
    PermissionDeniedError,
    SupabaseIntegrationError,
    UploadError,
)
from src.database.supabase_integration.tests.fakes.logger import CaptureLogger

SECRET = "sb_secret_PLANTED_KEY_123"
BASE = "https://proj.supabase.test"


class FakeTusServer:
    def __init__(self, *, create_status=201):
        self.create_status = create_status
        self.requests: list[httpx.Request] = []
        self.received = bytearray()
        self.length = 0
        self.fail_patch: list = []  # itens: "drop" (perde a conexão após gravar metade) | int status | "lose" (grava e perde)
        self.head_status = 200

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if request.method == "POST":
            if self.create_status != 201:
                return httpx.Response(self.create_status, json={"statusCode": str(self.create_status), "error": "Duplicate",
                                                                 "message": "The resource already exists"})
            self.length = int(request.headers["Upload-Length"])
            return httpx.Response(201, headers={"Location": "/storage/v1/upload/resumable/abc123"})
        if request.method == "HEAD":
            if self.head_status != 200:
                return httpx.Response(self.head_status)
            return httpx.Response(200, headers={"Upload-Offset": str(len(self.received))})
        if request.method == "PATCH":
            assert int(request.headers["Upload-Offset"]) == len(self.received), "offset fora de sincronia"
            action = self.fail_patch.pop(0) if self.fail_patch else None
            body = request.content
            if action == "drop":
                self.received += body[: len(body) // 2]
                raise httpx.ReadError("conexão perdida", request=request)
            if action == "lose":
                self.received += body
                raise httpx.ReadTimeout("resposta perdida", request=request)
            if isinstance(action, int):
                return httpx.Response(action, headers={"Retry-After": "0"}, json={"message": "falha"})
            self.received += body
            return httpx.Response(204, headers={"Upload-Offset": str(len(self.received))})
        raise AssertionError(request.method)


def client(server, **kw):
    http = httpx.Client(transport=httpx.MockTransport(server))
    kw.setdefault("sleep", lambda s: None)
    return TusClient(BASE, lambda: SECRET, http_client=http, **kw)


def data(n):
    return bytes(i % 251 for i in range(n))


def test_creation_headers_and_chunked_patches():
    srv = FakeTusServer()
    payload = data(2500)
    client(srv).upload("media", "a/b.bin", io.BytesIO(payload), len(payload), content_type="video/mp4",
                       cache_control_seconds=3600, metadata={"original_name": "Aula 1.mp4"}, chunk_bytes=1000)
    post, *patches = srv.requests
    assert str(post.url) == f"{BASE}/storage/v1/upload/resumable"
    assert post.headers["Tus-Resumable"] == "1.0.0" and post.headers["Upload-Length"] == "2500"
    assert "x-upsert" not in post.headers
    meta = dict(kv.split(" ", 1) for kv in post.headers["Upload-Metadata"].split(","))
    decoded = {k: base64.b64decode(v).decode() for k, v in meta.items()}
    assert decoded["bucketName"] == "media" and decoded["objectName"] == "a/b.bin"
    assert decoded["contentType"] == "video/mp4" and decoded["cacheControl"] == "3600"
    assert "Aula 1.mp4" in decoded["metadata"]
    assert [p.headers["Upload-Offset"] for p in patches] == ["0", "1000", "2000"]
    assert all(p.headers["Content-Type"] == "application/offset+octet-stream" for p in patches)
    assert [len(p.content) for p in patches] == [1000, 1000, 500]
    assert patches[0].url.path == "/storage/v1/upload/resumable/abc123"
    assert bytes(srv.received) == payload


def test_upsert_sets_header_and_path_source(tmp_path):
    f = tmp_path / "x.bin"
    f.write_bytes(data(300))
    srv = FakeTusServer()
    client(srv).upload("b", "p.bin", f, 300, upsert=True, chunk_bytes=200)
    assert srv.requests[0].headers["x-upsert"] == "true"
    assert bytes(srv.received) == data(300)


def test_custom_resumable_url_override():
    srv = FakeTusServer()
    http = httpx.Client(transport=httpx.MockTransport(srv))
    TusClient(BASE, lambda: SECRET, http_client=http, resumable_url="https://ref.storage.supabase.test/storage/v1/upload/resumable").upload(
        "b", "p", io.BytesIO(b"abc"), 3)
    assert srv.requests[0].url.host == "ref.storage.supabase.test"


def test_resumes_from_server_offset_after_connection_drop_without_resending_confirmed_chunks():
    srv = FakeTusServer()
    srv.fail_patch = [None, "drop"]  # 1º chunk ok; 2º cai no meio (servidor guardou metade)
    payload = data(3000)
    log = CaptureLogger()
    client(srv, logger=log).upload("b", "p", io.BytesIO(payload), 3000, chunk_bytes=1000)
    assert bytes(srv.received) == payload
    offsets = [int(r.headers["Upload-Offset"]) for r in srv.requests if r.method == "PATCH"]
    assert offsets == [0, 1000, 1500, 2000]  # os 500 bytes já confirmados (1000..1500) não foram reenviados
    assert sum(1 for r in srv.requests if r.method == "HEAD") == 1
    assert log.levels() == ["WARNING"]


def test_resume_after_lost_response_and_transient_status():
    srv = FakeTusServer()
    srv.fail_patch = ["lose", 503]
    payload = data(2000)
    client(srv).upload("b", "p", io.BytesIO(payload), 2000, chunk_bytes=1000)
    assert bytes(srv.received) == payload


def test_non_seekable_source_still_resumes_inside_current_chunk():
    class OneWay(io.RawIOBase):
        def __init__(self, b):
            self.b = io.BytesIO(b)

        def readable(self):
            return True

        def seekable(self):
            return False

        def readinto(self, buf):
            d = self.b.read(len(buf))
            buf[: len(d)] = d
            return len(d)

    srv = FakeTusServer()
    srv.fail_patch = [None, "drop"]
    payload = data(3000)
    client(srv).upload("b", "p", OneWay(payload), 3000, chunk_bytes=1000)
    assert bytes(srv.received) == payload


def test_gives_up_after_max_resume_attempts_with_domain_error():
    srv = FakeTusServer()
    srv.fail_patch = [503, 503, 503, 503]
    with pytest.raises(SupabaseIntegrationError) as ei:
        client(srv, max_resume_attempts=2).upload("b", "p", io.BytesIO(b"x" * 10), 10)
    assert not isinstance(ei.value, httpx.HTTPError)


def test_expired_upload_url_requires_restart():
    srv = FakeTusServer()
    srv.fail_patch = ["drop"]
    srv.head_status = 404
    with pytest.raises(UploadError) as ei:
        client(srv).upload("b", "p", io.BytesIO(b"x" * 10), 10)
    assert ei.value.outcome_unknown


def test_conflict_on_create_becomes_domain_error():
    srv = FakeTusServer(create_status=409)
    with pytest.raises(SupabaseIntegrationError) as ei:
        client(srv).upload("b", "p", io.BytesIO(b"abc"), 3)
    assert isinstance(ei.value, FileAlreadyExistsError), type(ei.value)
    assert len(srv.requests) == 1  # nada foi enviado


def test_forbidden_on_create_is_permission_denied_and_key_never_leaks():
    srv = FakeTusServer(create_status=403)
    log = CaptureLogger()
    with pytest.raises(SupabaseIntegrationError) as ei:
        client(srv, logger=log).upload("b", "p", io.BytesIO(b"abc"), 3)
    assert isinstance(ei.value, PermissionDeniedError)
    assert SECRET not in str(ei.value) and SECRET not in repr(ei.value.to_dict())
    assert SECRET not in repr(log.events)


def test_source_shorter_than_declared_size_fails_clearly():
    srv = FakeTusServer()
    with pytest.raises(UploadError):
        client(srv).upload("b", "p", io.BytesIO(b"abc"), 10, chunk_bytes=5)


def test_metadata_builder_omits_missing_fields():
    raw = build_upload_metadata("b", "p", None, None, None)
    assert [kv.split(" ")[0] for kv in raw.split(",")] == ["bucketName", "objectName"]
