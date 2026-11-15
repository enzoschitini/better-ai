"""Utilitários de FileSource (sem ler tudo para a memória)."""
import io

import pytest

from bai_supabase.contracts.storage import BytesSource, PathSource, StreamSource
from bai_supabase.errors.exceptions import FileTooLargeError, ValidationError
from bai_supabase.storage.sources import prepare_source

KW = dict(max_bytes=10_000_000, memory_cap_bytes=1_000)
PNG = b"\x89PNG\r\n\x1a\n" + b"\x01" * 100


def test_path_source_size_head_and_reopen(tmp_path):
    f = tmp_path / "foto.png"
    f.write_bytes(PNG * 200)
    with prepare_source(PathSource(f), **KW) as p:
        assert p.size == len(PNG) * 200 and p.filename == "foto.png" and p.restartable
        assert p.head == (PNG * 200)[:8192]
        for _ in range(2):  # reabre do início
            with p.open() as h:
                assert h.read(8) == PNG[:8]


def test_path_source_missing_is_validation_error(tmp_path):
    with pytest.raises(ValidationError):
        prepare_source(PathSource(tmp_path / "nao-existe.bin"), **KW)
    with pytest.raises(ValidationError):
        prepare_source(PathSource(tmp_path), **KW)


def test_bytes_source_cap_directs_to_path_or_stream():
    with prepare_source(BytesSource(b"x" * 1000, filename="a.bin"), **KW) as p:
        assert p.size == 1000 and p.data == b"x" * 1000
    with pytest.raises(ValidationError, match="PathSource ou StreamSource"):
        prepare_source(BytesSource(b"x" * 1001), **KW)


def test_seekable_stream_with_size_restartable_flag_and_no_close():
    s = io.BytesIO(b"abc" * 100)
    s.read(3)  # posição inicial não é zero
    with prepare_source(StreamSource(s, size=297, restartable=True), **KW) as p:
        assert p.restartable and p.head[:3] == b"abc"
        with p.open() as h:
            assert h.read(3) == b"abc"
        with p.open() as h:
            assert len(h.read()) == 297
    assert not s.closed
    with prepare_source(StreamSource(io.BytesIO(b"z"), size=1, restartable=False), **KW) as p2:
        assert not p2.restartable


class _OneWay(io.RawIOBase):
    """Stream não rebobinável."""

    def __init__(self, data):
        self._b = io.BytesIO(data)

    def readable(self):
        return True

    def seekable(self):
        return False

    def readinto(self, buf):
        d = self._b.read(len(buf))
        buf[: len(d)] = d
        return len(d)


def test_non_seekable_stream_head_is_returned_to_stream_and_not_restartable():
    data = PNG * 5
    with prepare_source(StreamSource(_OneWay(data), size=len(data), restartable=True), **KW) as p:
        assert not p.restartable and p.head == data
        with p.open() as h:
            assert h.read() == data  # o trecho lido para detecção não se perde
        with pytest.raises(ValidationError):
            with p.open():
                pass


def test_unknown_size_stream_spooled_counts_and_is_restartable():
    data = b"q" * 5000
    with prepare_source(StreamSource(_OneWay(data)), max_bytes=10_000, memory_cap_bytes=100, spool_memory_bytes=1024) as p:
        assert p.size == 5000 and p.restartable and p.head == data[:5000]
        with p.open() as h:
            assert h.read() == data
        with p.open() as h:
            assert h.read(10) == data[:10]


def test_unknown_size_stream_aborts_above_limit():
    with pytest.raises(FileTooLargeError):
        prepare_source(StreamSource(_OneWay(b"q" * 5000)), max_bytes=4000, memory_cap_bytes=100)


def test_invalid_source_type():
    with pytest.raises(ValidationError):
        prepare_source("caminho.txt", **KW)  # type: ignore[arg-type]
