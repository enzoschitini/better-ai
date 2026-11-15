"""Utilitários para ``FileSource`` (caminho | bytes | stream) sem carregar tudo em memória.

``prepare_source`` lê só os primeiros bytes (para a detecção de tipo), descobre o tamanho e devolve
um ``PreparedSource`` que sabe ABRIR a fonte (de novo, se for reiniciável). Streams sem tamanho
conhecido são copiados para um arquivo temporário (contando bytes e abortando acima do teto),
o que também os torna reiniciáveis; o temporário é removido em ``close()``.
"""

from __future__ import annotations

import io
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, Callable, ContextManager, Iterator, Optional

from bai_supabase.contracts.storage import BytesSource, FileSource, PathSource, StreamSource
from bai_supabase.errors.exceptions import FileTooLargeError, ValidationError
from bai_supabase.storage.validators import HEAD_BYTES

_COPY_CHUNK = 1024 * 1024


class PreparedSource:
    """Fonte pronta: tamanho, cabeçalho (magic bytes), nome e abertura reiniciável."""

    def __init__(
        self,
        *,
        size: int,
        head: bytes,
        filename: Optional[str],
        declared_content_type: Optional[str],
        restartable: bool,
        opener: Callable[[], ContextManager[BinaryIO]],
        data: Optional[bytes] = None,
        cleanup: Optional[Callable[[], None]] = None,
    ) -> None:
        self.size = size
        self.head = head
        self.filename = filename
        self.declared_content_type = declared_content_type
        #: O executor só pode repetir a operação se a fonte puder ser relida do início.
        self.restartable = restartable
        #: Bytes já em memória (somente ``BytesSource``); ``None`` nos demais.
        self.data = data
        self._opener = opener
        self._cleanup = cleanup

    def open(self) -> ContextManager[BinaryIO]:
        """Abre a fonte posicionada no início (cada tentativa reabre)."""
        return self._opener()

    def close(self) -> None:
        if self._cleanup is not None:
            self._cleanup()
            self._cleanup = None

    def __enter__(self) -> "PreparedSource":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


class _PrefixedStream(io.RawIOBase):
    """Devolve ``prefix`` e depois o restante de ``stream`` (para stream não rebobinável)."""

    def __init__(self, prefix: bytes, stream: BinaryIO) -> None:
        self._prefix = memoryview(prefix)
        self._stream = stream

    def readable(self) -> bool:
        return True

    def readinto(self, buffer) -> int:
        if len(self._prefix):
            n = min(len(buffer), len(self._prefix))
            buffer[:n] = self._prefix[:n]
            self._prefix = self._prefix[n:]
            return n
        data = self._stream.read(len(buffer))
        buffer[: len(data)] = data
        return len(data)


def _is_seekable(stream: BinaryIO) -> bool:
    try:
        return bool(stream.seekable())
    except (AttributeError, ValueError, OSError):
        return False


def prepare_source(
    source: FileSource,
    *,
    max_bytes: int,
    memory_cap_bytes: int,
    spool_memory_bytes: int = 6 * 1024 * 1024,
    head_bytes: int = HEAD_BYTES,
) -> PreparedSource:
    """Prepara a fonte. ``FileTooLargeError`` se (ou assim que) passar de ``max_bytes``."""
    if isinstance(source, PathSource):
        return _prepare_path(source, head_bytes)
    if isinstance(source, BytesSource):
        return _prepare_bytes(source, head_bytes, memory_cap_bytes)
    if isinstance(source, StreamSource):
        return _prepare_stream(source, head_bytes, max_bytes, spool_memory_bytes)
    raise ValidationError("fonte de arquivo inválida (use PathSource, BytesSource ou StreamSource)")


def _prepare_path(source: PathSource, head_bytes: int) -> PreparedSource:
    path = Path(source.path)
    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            head = handle.read(head_bytes)
    except (FileNotFoundError, NotADirectoryError, IsADirectoryError, PermissionError) as exc:
        raise ValidationError("arquivo de origem inexistente ou ilegível", operation="storage.upload") from exc

    @contextmanager
    def opener() -> Iterator[BinaryIO]:
        with path.open("rb") as handle:
            yield handle

    return PreparedSource(
        size=size,
        head=head,
        filename=source.filename or path.name,
        declared_content_type=source.content_type,
        restartable=True,
        opener=opener,
    )


def _prepare_bytes(source: BytesSource, head_bytes: int, memory_cap_bytes: int) -> PreparedSource:
    data = source.data
    if len(data) > memory_cap_bytes:
        raise ValidationError(
            f"bytes em memória ({len(data)}) excedem o teto de {memory_cap_bytes}; use PathSource ou StreamSource",
            operation="storage.upload",
        )

    @contextmanager
    def opener() -> Iterator[BinaryIO]:
        yield io.BytesIO(data)

    return PreparedSource(
        size=len(data),
        head=data[:head_bytes],
        filename=source.filename,
        declared_content_type=source.content_type,
        restartable=True,
        opener=opener,
        data=data,
    )


def _prepare_stream(source: StreamSource, head_bytes: int, max_bytes: int, spool_memory_bytes: int) -> PreparedSource:
    if source.size is None:
        return _spool_stream(source, head_bytes, max_bytes, spool_memory_bytes)
    stream = source.stream
    if _is_seekable(stream):
        start = stream.tell()
        head = stream.read(head_bytes)
        stream.seek(start)

        @contextmanager
        def seekable_opener() -> Iterator[BinaryIO]:
            stream.seek(start)
            yield stream  # o chamador é o dono do stream: não fechamos

        return PreparedSource(
            size=source.size, head=head, filename=source.filename, declared_content_type=source.content_type,
            restartable=bool(source.restartable), opener=seekable_opener,
        )
    head = stream.read(head_bytes)
    chained = _PrefixedStream(head, stream)
    used = {"opened": False}

    @contextmanager
    def one_shot_opener() -> Iterator[BinaryIO]:
        if used["opened"]:
            raise ValidationError("stream não reiniciável já foi consumido", operation="storage.upload")
        used["opened"] = True
        yield chained  # type: ignore[misc]

    return PreparedSource(
        size=source.size, head=head, filename=source.filename, declared_content_type=source.content_type,
        restartable=False, opener=one_shot_opener,
    )


def _spool_stream(source: StreamSource, head_bytes: int, max_bytes: int, spool_memory_bytes: int) -> PreparedSource:
    """Stream sem tamanho: copia para temporário contando bytes; aborta ao passar de ``max_bytes``."""
    spool = tempfile.SpooledTemporaryFile(max_size=spool_memory_bytes, mode="w+b")  # noqa: SIM115
    total = 0
    try:
        while True:
            chunk = source.stream.read(_COPY_CHUNK)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise FileTooLargeError(
                    f"stream excede o limite de {max_bytes} bytes", operation="storage.upload"
                )
            spool.write(chunk)
        spool.seek(0)
        head = spool.read(head_bytes)
    except BaseException:
        spool.close()
        raise

    @contextmanager
    def opener() -> Iterator[BinaryIO]:
        spool.seek(0)
        yield spool  # type: ignore[misc]

    return PreparedSource(
        size=total, head=head, filename=source.filename, declared_content_type=source.content_type,
        restartable=True, opener=opener, cleanup=spool.close,
    )
