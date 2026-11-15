"""Cliente TUS mínimo sobre ``httpx`` para o upload resumable do Supabase Storage.

ATENÇÃO: o protocolo abaixo segue a documentação consultada em research/07 §2 (endpoint
``<projeto>/storage/v1/upload/resumable``, chunk fixo de 6 MiB, ``Tus-Resumable: 1.0.0``,
``Upload-Metadata`` com ``bucketName``/``objectName``/``contentType``/``cacheControl``, header
``x-upsert``, retomada por ``HEAD`` do offset). DEVE ser confirmado contra a documentação oficial
e contra um projeto real na integração (tarefas T-005 e T-306): nomes de cabeçalhos/metadados e o
limite efetivo de tamanho não foram verificados em rede.

Segurança: a chave vem de um provedor injetado e só é colocada no cabeçalho ``Authorization``;
nunca é registrada nem entra em mensagens. Erros HTTP/transporte viram exceções do domínio via
``sdk_errors``. Memória: no máximo 1 chunk por vez (mais o buffer de reenvio do mesmo chunk).
"""

from __future__ import annotations

import base64
import json
import time
from pathlib import Path
from typing import BinaryIO, Callable, Optional, Union
from urllib.parse import urljoin

import httpx

from bai_supabase.adapters.normalize import sdk_errors
from bai_supabase.contracts.logging import LoggerContract
from bai_supabase.errors.exceptions import UploadError

TUS_VERSION = "1.0.0"
DEFAULT_CHUNK_BYTES = 6 * 1024 * 1024
RESUMABLE_PATH = "/storage/v1/upload/resumable"
_TRANSIENT_STATUS = frozenset({408, 423, 429, 500, 502, 503, 504})
_MAX_RETRY_AFTER = 30.0


def _b64(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def build_upload_metadata(
    bucket: str, path: str, content_type: Optional[str], cache_control_seconds: Optional[int], metadata: Optional[dict]
) -> str:
    """Valor do cabeçalho ``Upload-Metadata`` (pares ``chave base64(valor)`` separados por vírgula)."""
    pairs = {"bucketName": bucket, "objectName": path}
    if content_type:
        pairs["contentType"] = content_type
    if cache_control_seconds is not None:
        pairs["cacheControl"] = str(cache_control_seconds)
    if metadata:
        pairs["metadata"] = json.dumps(metadata, ensure_ascii=False)
    return ",".join(f"{k} {_b64(v)}" for k, v in pairs.items())


class _ChunkReader:
    """Entrega o chunk de um offset; guarda só o último chunk para reenviar sem reler a fonte."""

    def __init__(self, handle: BinaryIO, size: int, chunk_bytes: int) -> None:
        self._handle = handle
        self._size = size
        self._chunk = chunk_bytes
        self._pos = 0  # posição lógica da fonte
        self._buf = b""
        self._buf_start = 0

    def _seekable(self) -> bool:
        try:
            return bool(self._handle.seekable())
        except (AttributeError, ValueError, OSError):
            return False

    def _read_exact(self, n: int) -> bytes:
        parts, remaining = [], n
        while remaining > 0:
            part = self._handle.read(remaining)
            if not part:
                break
            parts.append(part)
            remaining -= len(part)
        return b"".join(parts)

    def get(self, offset: int) -> bytes:
        if self._buf_start <= offset < self._buf_start + len(self._buf):
            return self._buf[offset - self._buf_start :]
        if offset != self._pos:
            if not self._seekable():
                raise UploadError(
                    "retomada exige reler a fonte, mas ela não é rebobinável", operation="storage.upload_resumable",
                    outcome_unknown=True,
                )
            self._handle.seek(offset)
            self._pos = offset
        data = self._read_exact(min(self._chunk, self._size - offset))
        if not data:
            raise UploadError("a fonte terminou antes do tamanho declarado", operation="storage.upload_resumable")
        self._buf, self._buf_start = data, offset
        self._pos = offset + len(data)
        return data


class TusClient:
    """Upload resumable TUS 1.0.0 (criação + PATCH por chunk + retomada por HEAD)."""

    def __init__(
        self,
        project_url: str,
        key_provider: Callable[[], str],
        *,
        http_client: Optional[httpx.Client] = None,
        resumable_url: Optional[str] = None,
        max_resume_attempts: int = 3,
        backoff_base_seconds: float = 0.5,
        sleep: Callable[[float], None] = time.sleep,
        logger: Optional[LoggerContract] = None,
    ) -> None:
        self._endpoint = resumable_url or project_url.rstrip("/") + RESUMABLE_PATH
        self._key = key_provider
        self._http = http_client or httpx.Client(timeout=httpx.Timeout(120.0, connect=3.0))
        self._max_resume = max_resume_attempts
        self._backoff = backoff_base_seconds
        self._sleep = sleep
        self._log = logger

    # ------------------------------------------------------------------ API
    def upload(
        self,
        bucket: str,
        path: str,
        source: Union[BinaryIO, str, Path],
        size: int,
        *,
        content_type: Optional[str] = None,
        upsert: bool = False,
        cache_control_seconds: Optional[int] = None,
        metadata: Optional[dict] = None,
        chunk_bytes: int = DEFAULT_CHUNK_BYTES,
    ) -> None:
        resource = f"{bucket}/{path}"
        opened = isinstance(source, (str, Path))
        handle: BinaryIO = open(source, "rb") if opened else source  # type: ignore[arg-type,assignment]
        try:
            with sdk_errors("storage", "storage.upload_resumable", resource):
                location = self._create(bucket, path, size, content_type, upsert, cache_control_seconds, metadata)
                self._transfer(location, _ChunkReader(handle, size, chunk_bytes), size, resource)
        finally:
            if opened:
                handle.close()

    # ------------------------------------------------------------ protocolo
    def _headers(self, **extra: str) -> dict:
        return {"Authorization": f"Bearer {self._key()}", "Tus-Resumable": TUS_VERSION, **extra}

    def _create(self, bucket, path, size, content_type, upsert, cache_control_seconds, metadata) -> str:
        extra = {
            "Upload-Length": str(size),
            "Upload-Metadata": build_upload_metadata(bucket, path, content_type, cache_control_seconds, metadata),
        }
        if upsert:
            extra["x-upsert"] = "true"
        response = self._http.post(self._endpoint, headers=self._headers(**extra))
        response.raise_for_status()
        location = response.headers.get("Location")
        if not location:
            raise UploadError("resposta de criação TUS sem Location", operation="storage.upload_resumable")
        return urljoin(self._endpoint, location)

    def _transfer(self, location: str, reader: _ChunkReader, size: int, resource: str) -> None:
        offset, failures = 0, 0
        while offset < size:
            chunk = reader.get(offset)
            problem: Optional[BaseException] = None
            retry_after: Optional[float] = None
            try:
                response = self._http.patch(
                    location,
                    content=chunk,
                    headers=self._headers(**{
                        "Upload-Offset": str(offset), "Content-Type": "application/offset+octet-stream",
                    }),
                )
            except httpx.TransportError as exc:
                problem = exc
            else:
                if response.status_code in _TRANSIENT_STATUS:
                    problem = _status_error(response)
                    retry_after = _retry_after(response)
                else:
                    response.raise_for_status()
                    offset = int(response.headers.get("Upload-Offset", offset + len(chunk)))
                    continue
            failures += 1
            if failures > self._max_resume:
                raise problem
            self._warn("upload resumable: retomando do offset do servidor", resource, failures, offset)
            self._sleep(retry_after if retry_after is not None else self._backoff * (2 ** (failures - 1)))
            offset = self._server_offset(location, resource)

    def _server_offset(self, location: str, resource: str) -> int:
        response = self._http.head(location, headers=self._headers())
        if response.status_code in (404, 410):
            raise UploadError(
                "URL de upload expirada ou inexistente: recomece o upload do zero",
                operation="storage.upload_resumable", resource=resource, status=response.status_code,
                outcome_unknown=True,
            )
        response.raise_for_status()
        return int(response.headers.get("Upload-Offset", "0"))

    def _warn(self, event: str, resource: str, attempt: int, offset: int) -> None:
        if self._log is not None:
            self._log.warning(event, operation="storage.upload_resumable", resource=resource, attempt=attempt, offset=offset)


def _status_error(response: httpx.Response) -> httpx.HTTPStatusError:
    return httpx.HTTPStatusError(
        f"HTTP {response.status_code}", request=response.request, response=response
    )


def _retry_after(response: httpx.Response) -> Optional[float]:
    raw = response.headers.get("Retry-After")
    try:
        return min(float(raw), _MAX_RETRY_AFTER) if raw is not None else None
    except ValueError:
        return None
