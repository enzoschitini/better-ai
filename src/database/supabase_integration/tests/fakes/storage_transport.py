"""Transporte de storage em memória (implementa ``StorageTransport``) para testes offline."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, BinaryIO, Optional, Sequence, Union

from src.database.supabase_integration.contracts.transports import TransportObject
from src.database.supabase_integration.errors.exceptions import (
    FileAlreadyExistsError,
    FileNotFoundInStorageError,
    SupabaseIntegrationError,
)


@dataclass
class StoredObject:
    data: bytes
    content_type: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    cache_control_seconds: Optional[int] = None
    mode: str = "standard"
    size: Optional[int] = None  # usado quando keep_data=False (dados descartados)

    @property
    def length(self) -> int:
        return len(self.data) if self.size is None else self.size


class InMemoryStorageTransport:
    """Buckets em memória: conflito/upsert, listagem com offset, URL assinada fictícia, resumable simulado."""

    def __init__(self, keep_data: bool = True) -> None:
        #: False: descarta o conteúdo no resumable (testes de arquivo grande sem alocar tudo).
        self.keep_data = keep_data
        self.objects: dict[tuple[str, str], StoredObject] = {}
        self.calls: list[tuple[str, tuple]] = []
        self.failures: dict[str, list[SupabaseIntegrationError]] = {}
        self.chunks_read: list[int] = []  # tamanhos dos blocos lidos no resumable
        self.max_chunk_seen = 0

    # --- apoio de teste
    def fail_next(self, method: str, error: SupabaseIntegrationError, times: int = 1) -> None:
        self.failures.setdefault(method, []).extend([error] * times)

    def put(self, bucket: str, path: str, data: bytes, content_type: Optional[str] = None) -> None:
        self.objects[(bucket, path)] = StoredObject(data, content_type)

    def called(self, method: str) -> int:
        return sum(1 for name, _ in self.calls if name == method)

    def _enter(self, method: str, *args: Any) -> None:
        self.calls.append((method, args))
        queue = self.failures.get(method)
        if queue:
            raise queue.pop(0)

    # --- upload
    def _store(
        self, bucket, path, data: bytes, *, content_type, upsert, cache_control_seconds, metadata, mode,
        size: Optional[int] = None,
    ) -> None:
        if (bucket, path) in self.objects and not upsert:
            raise FileAlreadyExistsError("objeto já existe", operation="storage.upload", resource=f"{bucket}/{path}")
        self.objects[(bucket, path)] = StoredObject(
            data, content_type, dict(metadata or {}), cache_control_seconds, mode, size
        )

    def upload_standard(
        self, bucket: str, path: str, data: Union[bytes, BinaryIO, str, Path], *, content_type: Optional[str] = None,
        upsert: bool = False, cache_control_seconds: Optional[int] = None, metadata: Optional[dict] = None,
    ) -> None:
        self._enter("upload_standard", bucket, path)
        if isinstance(data, (str, Path)):
            payload = Path(data).read_bytes()
        elif isinstance(data, (bytes, bytearray)):
            payload = bytes(data)
        else:
            payload = data.read()
        self._store(bucket, path, payload, content_type=content_type, upsert=upsert,
                    cache_control_seconds=cache_control_seconds, metadata=metadata, mode="standard")

    def upload_resumable(
        self, bucket: str, path: str, source: Union[BinaryIO, str, Path], size: int, *, content_type: Optional[str] = None,
        upsert: bool = False, cache_control_seconds: Optional[int] = None, metadata: Optional[dict] = None,
        chunk_bytes: int = 6 * 1024 * 1024,
    ) -> None:
        self._enter("upload_resumable", bucket, path)
        if (bucket, path) in self.objects and not upsert:
            raise FileAlreadyExistsError("objeto já existe", operation="storage.upload", resource=f"{bucket}/{path}")
        handle = open(source, "rb") if isinstance(source, (str, Path)) else source
        parts: list[bytes] = []
        try:
            received = 0
            while received < size:
                chunk = handle.read(min(chunk_bytes, size - received))
                if not chunk:
                    break
                self.chunks_read.append(len(chunk))
                self.max_chunk_seen = max(self.max_chunk_seen, len(chunk))
                if self.keep_data:
                    parts.append(chunk)
                received += len(chunk)
        finally:
            if isinstance(source, (str, Path)):
                handle.close()
        self._store(bucket, path, b"".join(parts), content_type=content_type, upsert=upsert,
                    cache_control_seconds=cache_control_seconds, metadata=metadata, mode="resumable",
                    size=None if self.keep_data else received)

    # --- leitura
    def _get(self, bucket: str, path: str) -> StoredObject:
        try:
            return self.objects[(bucket, path)]
        except KeyError:
            raise FileNotFoundInStorageError("objeto não encontrado (ou sem permissão)", resource=f"{bucket}/{path}") from None

    def download_bytes(self, bucket: str, path: str) -> bytes:
        self._enter("download_bytes", bucket, path)
        return self._get(bucket, path).data

    def download_to_file(self, bucket: str, path: str, destination: Path) -> Path:
        self._enter("download_to_file", bucket, path)
        obj = self._get(bucket, path)
        tmp = destination.with_name(destination.name + ".part")
        tmp.write_bytes(obj.data)
        os.replace(tmp, destination)
        return destination

    def object_size(self, bucket: str, path: str) -> Optional[int]:
        self._enter("object_size", bucket, path)
        return self._get(bucket, path).length

    def create_signed_url(self, bucket: str, path: str, expires_in: int) -> str:
        self._enter("create_signed_url", bucket, path, expires_in)
        return f"https://fake.invalid/storage/v1/object/sign/{bucket}/{path}?token=FAKE-SIGNED-TOKEN&exp={expires_in}"

    def public_url(self, bucket: str, path: str) -> str:
        self._enter("public_url", bucket, path)
        return f"https://fake.invalid/storage/v1/object/public/{bucket}/{path}"

    def exists(self, bucket: str, path: str) -> bool:
        self._enter("exists", bucket, path)
        return (bucket, path) in self.objects

    def list_objects(self, bucket: str, prefix: str, limit: int, offset: int, sort_by: str = "name") -> list[TransportObject]:
        self._enter("list_objects", bucket, prefix, limit, offset)
        base = f"{prefix.strip('/')}/" if prefix.strip("/") else ""
        children: dict[str, TransportObject] = {}
        for (b, p), obj in self.objects.items():
            if b != bucket or not p.startswith(base):
                continue
            rest = p[len(base):]
            name, slash, _ = rest.partition("/")
            if slash:
                children.setdefault(name, TransportObject(path=f"{base}{name}", name=name, is_folder=True))
            else:
                children[name] = TransportObject(
                    path=p, name=name, size=obj.length, content_type=obj.content_type, is_folder=False
                )
        rows = [children[k] for k in sorted(children)]
        return rows[offset : offset + limit]

    def remove(self, bucket: str, paths: Sequence[str]) -> list[str]:
        self._enter("remove", bucket, tuple(paths))
        removed = []
        for p in paths:
            if self.objects.pop((bucket, p), None) is not None:
                removed.append(p)
        return removed
