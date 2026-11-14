"""``StorageTransport`` sobre o cliente SÍNCRONO do supabase-py / storage3.

Único lugar (com ``tus.py``) que fala com o SDK e com ``httpx`` na frente de arquivos. TODA chamada
fica dentro de ``sdk_errors``: nenhuma exceção do SDK/``httpx`` escapa. O cliente chega por um
PROVEDOR injetado (``client_provider``), sem importar o SDK aqui.

Segurança: URLs assinadas nunca são logadas; no ``download_to_file`` a URL é curta (60 s), usada só
em memória, e o conteúdo vai direto para disco em blocos (escrita em ``.part`` + ``os.replace``).
"""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Any, BinaryIO, Callable, Optional, Protocol, Sequence, Union

import httpx

from bai_supabase.adapters.normalize import sdk_errors
from bai_supabase.contracts.transports import TransportObject
from bai_supabase.errors.exceptions import ConfigurationError

DEFAULT_CHUNK_BYTES = 6 * 1024 * 1024
_DOWNLOAD_BLOCK = 1024 * 1024
_DOWNLOAD_URL_TTL = 60
_FOLDER_PLACEHOLDER_ID = None


class ResumableUploader(Protocol):
    """Quem sabe fazer upload resumable (``adapters.tus.TusClient`` é a implementação padrão)."""

    def upload(
        self, bucket: str, path: str, source: Union[BinaryIO, str, Path], size: int, *,
        content_type: Optional[str] = ..., upsert: bool = ..., cache_control_seconds: Optional[int] = ...,
        metadata: Optional[dict] = ..., chunk_bytes: int = ...,
    ) -> None: ...


class SupabaseStorageTransport:
    """Implementa ``StorageTransport`` (contracts/transports.py) sobre ``client.storage.from_(bucket)``."""

    def __init__(
        self,
        client_provider: Callable[[], Any],
        *,
        resumable: Optional[ResumableUploader] = None,
        http_client: Optional[httpx.Client] = None,
        download_timeout: Optional[httpx.Timeout] = None,
    ) -> None:
        self._client_provider = client_provider
        self._resumable = resumable
        self._http = http_client or httpx.Client(timeout=download_timeout or httpx.Timeout(120.0, connect=3.0))

    def _bucket(self, bucket: str) -> Any:
        return self._client_provider().storage.from_(bucket)

    # ------------------------------------------------------------------ upload
    def upload_standard(
        self,
        bucket: str,
        path: str,
        data: Union[bytes, BinaryIO, str, Path],
        *,
        content_type: Optional[str] = None,
        upsert: bool = False,
        cache_control_seconds: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        options: dict = {"content-type": content_type or "application/octet-stream"}
        if upsert:
            options["upsert"] = "true"
        if cache_control_seconds is not None:
            options["cache-control"] = str(cache_control_seconds)
        if metadata:
            options["metadata"] = metadata
        payload, opened = self._payload(data)
        try:
            with sdk_errors("storage", "storage.upload", f"{bucket}/{path}"):
                self._bucket(bucket).upload(path, payload, options)
        finally:
            if opened is not None:
                opened.close()

    @staticmethod
    def _payload(data: Union[bytes, BinaryIO, str, Path]) -> tuple[Any, Optional[BinaryIO]]:
        """O SDK aceita bytes/BufferedReader/FileIO; caminho vira arquivo aberto (fechado por nós)."""
        if isinstance(data, (str, Path)):
            handle = open(data, "rb")
            return handle, handle
        if isinstance(data, (bytes, bytearray)):
            return bytes(data), None
        if isinstance(data, (io.BufferedReader, io.FileIO)):
            return data, None  # o SDK envia em streaming
        return data.read(), None  # outro file-like: o serviço só chega aqui até o limiar do modo padrão

    def upload_resumable(
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
        if self._resumable is None:
            raise ConfigurationError(
                "upload resumable não configurado neste transporte", operation="storage.upload_resumable",
                resource=f"{bucket}/{path}",
            )
        self._resumable.upload(  # já mapeia erros via sdk_errors
            bucket, path, source, size, content_type=content_type, upsert=upsert,
            cache_control_seconds=cache_control_seconds, metadata=metadata, chunk_bytes=chunk_bytes,
        )

    # ---------------------------------------------------------------- download
    def download_bytes(self, bucket: str, path: str) -> bytes:
        with sdk_errors("storage", "storage.download", f"{bucket}/{path}"):
            return self._bucket(bucket).download(path)

    def download_to_file(self, bucket: str, path: str, destination: Path) -> Path:
        """Streaming para disco via URL assinada curta; ``.part`` + rename atômico (sem arquivo parcial)."""
        destination = Path(destination)
        part = destination.with_name(destination.name + ".part")
        url = self.create_signed_url(bucket, path, _DOWNLOAD_URL_TTL)
        try:
            with sdk_errors("storage", "storage.download_to", f"{bucket}/{path}"):
                with self._http.stream("GET", url) as response:
                    if response.status_code >= 400:
                        response.read()
                        response.raise_for_status()
                    with open(part, "wb") as out:
                        for block in response.iter_bytes(_DOWNLOAD_BLOCK):
                            out.write(block)
                os.replace(part, destination)
        except BaseException:
            part.unlink(missing_ok=True)
            raise
        return destination

    def object_size(self, bucket: str, path: str) -> Optional[int]:
        """Tamanho do objeto sem baixá-lo (capacidade opcional: ``SizedStorageTransport``)."""
        with sdk_errors("storage", "storage.info", f"{bucket}/{path}"):
            info = self._bucket(bucket).info(path) or {}
        size = info.get("size")
        if size is None:
            size = (info.get("metadata") or {}).get("size")
        return int(size) if size is not None else None

    # --------------------------------------------------------------------- URLs
    def create_signed_url(self, bucket: str, path: str, expires_in: int) -> str:
        with sdk_errors("storage", "storage.signed_url", f"{bucket}/{path}"):
            response = self._bucket(bucket).create_signed_url(path, expires_in)
            return response.get("signedURL") or response["signedUrl"]

    def public_url(self, bucket: str, path: str) -> str:
        with sdk_errors("storage", "storage.public_url", f"{bucket}/{path}"):
            return self._bucket(bucket).get_public_url(path)

    # ------------------------------------------------------------- meta / listagem
    def exists(self, bucket: str, path: str) -> bool:
        with sdk_errors("storage", "storage.exists", f"{bucket}/{path}"):
            return bool(self._bucket(bucket).exists(path))

    def list_objects(
        self, bucket: str, prefix: str, limit: int, offset: int, sort_by: str = "name"
    ) -> list[TransportObject]:
        options = {"limit": limit, "offset": offset, "sortBy": {"column": sort_by, "order": "asc"}}
        with sdk_errors("storage", "storage.list", f"{bucket}/{prefix}"):
            rows = self._bucket(bucket).list(prefix or "", options)
        return [self._to_object(prefix, row) for row in rows or []]

    @staticmethod
    def _to_object(prefix: str, row: dict) -> TransportObject:
        name = row["name"]
        base = prefix.strip("/")
        metadata = row.get("metadata") or {}
        is_folder = row.get("id") is _FOLDER_PLACEHOLDER_ID and not metadata  # pastas vêm sem id/metadados
        return TransportObject(
            path=f"{base}/{name}" if base else name,
            name=name,
            size=metadata.get("size"),
            content_type=metadata.get("mimetype"),
            updated_at=row.get("updated_at"),
            is_folder=is_folder,
        )

    def remove(self, bucket: str, paths: Sequence[str]) -> list[str]:
        with sdk_errors("storage", "storage.remove", f"{bucket}[{len(paths)} objetos]"):
            removed = self._bucket(bucket).remove(list(paths)) or []
        return [item["name"] for item in removed if isinstance(item, dict) and "name" in item]
