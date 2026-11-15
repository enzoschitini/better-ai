"""Validadores da classe de arquivos (research/05 §7, research/07 §4-§5)."""
import pytest

from src.database.supabase_integration.contracts.settings import StorageSettings
from src.database.supabase_integration.errors.exceptions import ConfigurationError, FileTooLargeError, ValidationError
from src.database.supabase_integration.storage.validators import (
    FileValidator,
    extension_of,
    is_mime_allowed,
    resolve_bucket,
    sanitize_original_name,
    slugify_filename,
    validate_object_path,
    validate_prefix,
    validate_size,
)

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
EXE = b"MZ\x90\x00" + b"\x00" * 64
MP3 = b"ID3\x03\x00\x00\x00\x00\x00\x00" + b"\x00" * 64


@pytest.mark.parametrize(
    "bad",
    [
        "../x.png", "a/../b.png", "/abs.png", "a\\b.png", "a/./b.png", "a//b.png", "a/b/", "a\x00b.png",
        "a\nb.png", "%2e%2e/x.png", "a/%2Fb.png", "%252e%252e/x", "C:/x.png", "con.txt", "a/NUL", "a/COM1.png",
        ".hidden", "a/.env", "a/b.", "caf\u00e9.png", "a b.png", "", "x/" + "y" * 300,
    ],
)
def test_path_traversal_and_unsafe_paths_rejected(bad):
    with pytest.raises(ValidationError):
        validate_object_path(bad)


def test_path_depth_and_length_limits():
    with pytest.raises(ValidationError):
        validate_object_path("/".join(["a"] * 9))
    with pytest.raises(ValidationError):
        validate_object_path("a/" * 2 + "b" * 1100)


def test_safe_path_accepted_and_normalized():
    assert validate_object_path("media/2026/11/abc-1.mp4") == "media/2026/11/abc-1.mp4"


def test_prefix_accepts_trailing_slash_and_empty_rules():
    assert validate_prefix("videos/2026/") == "videos/2026"
    assert validate_prefix("") == ""
    with pytest.raises(ValidationError):
        validate_prefix("", allow_empty=False)
    with pytest.raises(ValidationError):
        validate_prefix("../x")


def test_slugify_removes_accents_spaces_and_reserved():
    assert slugify_filename("Relatório Final (v2).PDF") == "relatorio-final-v2.pdf"
    assert slugify_filename("../../etc/passwd") == "passwd"
    assert slugify_filename("CON.txt") == "con-arquivo.txt"
    assert slugify_filename("...") == "arquivo"
    assert slugify_filename(".bashrc") == "bashrc"
    long = slugify_filename("a" * 400 + ".mp4")
    assert len(long) <= 100 and long.endswith(".mp4")


def test_original_name_keeps_readable_but_safe():
    assert sanitize_original_name("C:\\Users\\x\\Aula 01.mp4") == "Aula 01.mp4"
    assert sanitize_original_name("a\x00b\n.png") == "ab.png"
    assert sanitize_original_name(None) == "arquivo"
    assert len(sanitize_original_name("x" * 500 + ".mp4")) <= 255


def test_extension_of():
    assert extension_of("a.MP4") == ".mp4"
    assert extension_of("semext") == ""
    assert extension_of("a.tar.gz") == ".gz"
    assert extension_of("a.<script>") == ""


def test_bucket_default_allowlist_and_errors():
    s = StorageSettings(default_bucket="media")
    assert resolve_bucket(None, s) == "media"
    assert resolve_bucket("media", s) == "media"
    with pytest.raises(ValidationError):
        resolve_bucket("outro", s)
    s2 = StorageSettings(default_bucket="media", buckets_allowlist=("media", "docs"))
    assert resolve_bucket("docs", s2) == "docs"
    with pytest.raises(ValidationError):
        resolve_bucket("../etc", s2)
    with pytest.raises(ConfigurationError):
        resolve_bucket(None, StorageSettings())
    with pytest.raises(ConfigurationError):
        resolve_bucket("x", StorageSettings())


def test_size_rules():
    validate_size(10, 100)
    validate_size(None, 100)
    with pytest.raises(FileTooLargeError):
        validate_size(101, 100)
    with pytest.raises(ValidationError):
        validate_size(0, 100)


def test_mime_allowlist_wildcard():
    assert is_mime_allowed("image/png", ())
    assert is_mime_allowed("image/png", ("image/*",))
    assert not is_mime_allowed("video/mp4", ("image/*",))
    assert is_mime_allowed("video/mp4", ("image/*", "video/mp4"))


def _v(**kw):
    return FileValidator(StorageSettings(default_bucket="b", **kw))


def test_consistent_png_resolves_detected_type():
    assert _v().resolve_content_type(filename="a.png", declared="image/png", head=PNG) == "image/png"
    assert _v().resolve_content_type(filename="a.png", declared=None, head=PNG) == "image/png"
    assert _v().resolve_content_type(filename=None, declared=None, head=PNG) == "image/png"


def test_alias_mime_is_accepted_and_canonicalized():
    jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 32
    assert _v().resolve_content_type(filename="a.jpg", declared="image/jpg", head=jpeg) == "image/jpeg"


def test_extension_content_divergence_rejected_with_three_values():
    with pytest.raises(ValidationError) as ei:
        _v().resolve_content_type(filename="musica.mp3", declared="audio/mpeg", head=EXE)
    msg = str(ei.value)
    assert "extensão=audio/mpeg" in msg
    assert "declarado=audio/mpeg" in msg
    assert "detectado=application/x-msdownload" in msg


def test_binary_extension_with_unrecognized_content_rejected():
    with pytest.raises(ValidationError):
        _v().resolve_content_type(filename="foto.png", declared=None, head=b"nao e uma imagem" * 4)


def test_declared_differs_from_extension_rejected():
    with pytest.raises(ValidationError):
        _v().resolve_content_type(filename="a.png", declared="video/mp4", head=PNG)


def test_text_without_signature_is_accepted():
    ok = _v().resolve_content_type(filename="notas.txt", declared="text/plain; charset=utf-8", head=b"ola mundo")
    assert ok == "text/plain"
    generic = _v().resolve_content_type(filename="x.bin", declared="application/octet-stream", head=b"\x01\x02")
    assert generic == "application/octet-stream"


def test_allowed_mime_enforced_with_wildcard():
    v = _v(allowed_mime=("image/*",))
    assert v.resolve_content_type(filename="a.png", declared=None, head=PNG) == "image/png"
    with pytest.raises(ValidationError):
        v.resolve_content_type(filename="a.mp3", declared=None, head=MP3)


def test_dangerous_types_blocked_only_in_public_buckets():
    html = b"<html><script>alert(1)</script></html>"
    assert _v().resolve_content_type(filename="a.html", declared=None, head=html, public=False) == "text/html"
    with pytest.raises(ValidationError):
        _v().resolve_content_type(filename="a.html", declared=None, head=html, public=True)
    with pytest.raises(ValidationError):
        _v().resolve_content_type(filename="x.svg", declared=None, head=b"<svg/>", public=True)
