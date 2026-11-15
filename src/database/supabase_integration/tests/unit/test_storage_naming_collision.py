"""Nomeação e colisão (research/07 §6-§7)."""
import uuid
from datetime import datetime, timezone

import pytest

from src.database.supabase_integration.contracts.storage import CollisionPolicy, NamingStrategy
from src.database.supabase_integration.errors.exceptions import FileAlreadyExistsError, ValidationError
from src.database.supabase_integration.storage.collision import CollisionResolver, versioned_path
from src.database.supabase_integration.storage.naming import DatedUuidNaming, PreservedNameNaming
from src.database.supabase_integration.storage.validators import validate_object_path

FIXED = uuid.UUID("12345678-1234-5678-1234-567812345678")


def _naming():
    return DatedUuidNaming(clock=lambda: datetime(2026, 11, 3, tzinfo=timezone.utc), uuid_factory=lambda: FIXED)


def test_dated_uuid_default_layout_and_original_name_not_in_path():
    path = _naming().build_path(filename="Aula Secreta 01.MP4", folder="videos", content_type=None)
    assert path == f"videos/2026/11/{FIXED}.mp4"
    assert "aula" not in path.lower()


def test_dated_uuid_extension_from_content_type_and_no_folder():
    assert _naming().build_path(filename=None, folder=None, content_type="image/png") == f"2026/11/{FIXED}.png"
    assert _naming().build_path(filename="x", folder=None, content_type=None) == f"2026/11/{FIXED}"


def test_dated_uuid_unique_by_default_and_safe():
    n = DatedUuidNaming()
    a, b = (n.build_path(filename="a.png", folder="f", content_type=None) for _ in range(2))
    assert a != b and validate_object_path(a) == a


@pytest.mark.parametrize("folder", ["../x", "/abs", "a\\b", "a/../b"])
def test_naming_rejects_unsafe_folder(folder):
    with pytest.raises(ValidationError):
        _naming().build_path(filename="a.png", folder=folder, content_type=None)
    with pytest.raises(ValidationError):
        PreservedNameNaming().build_path(filename="a.png", folder=folder, content_type=None)


def test_preserved_name_slugifies_and_requires_name():
    p = PreservedNameNaming()
    out = p.build_path(filename="Relatório Final.PDF", folder="docs/2026", content_type=None)
    assert out == "docs/2026/relatorio-final.pdf"
    assert p.build_path(filename="../../x/Évil Name.png", folder=None, content_type=None) == "evil-name.png"
    with pytest.raises(ValidationError):
        p.build_path(filename=None, folder=None, content_type=None)


def test_strategies_implement_contract():
    assert isinstance(DatedUuidNaming(), NamingStrategy)
    assert isinstance(PreservedNameNaming(), NamingStrategy)


def test_versioned_path():
    assert versioned_path("a/b/c.mp4", 2) == "a/b/c-v2.mp4"
    assert versioned_path("a/b/c-v2.mp4", 3) == "a/b/c-v3.mp4"
    assert versioned_path("c", 2) == "c-v2"


def test_reject_has_no_lookup_and_no_upsert():
    calls = []
    r = CollisionResolver(lambda p: calls.append(p) or True).resolve("a/b.png", CollisionPolicy.REJECT)
    assert (r.path, r.upsert, calls) == ("a/b.png", False, [])


def test_overwrite_sets_upsert():
    r = CollisionResolver(lambda p: True).resolve("a/b.png", CollisionPolicy.OVERWRITE)
    assert r.upsert and r.path == "a/b.png"


def test_version_keeps_free_path_and_finds_next_free():
    taken = {"a/b.png", "a/b-v2.png"}
    res = CollisionResolver(lambda p: p in taken)
    assert res.resolve("x.png", CollisionPolicy.VERSION).path == "x.png"
    out = res.resolve("a/b.png", CollisionPolicy.VERSION)
    assert out.path == "a/b-v3.png" and out.versioned and not out.upsert


def test_version_exhaustion_raises():
    with pytest.raises(FileAlreadyExistsError):
        CollisionResolver(lambda p: True, max_versions=3).resolve("a.png", CollisionPolicy.VERSION)
