"""SupabaseSettings: imutável, composto por fatias, sem segredo em repr/str/resumo."""
from __future__ import annotations

import dataclasses
import pickle

import pytest

from src.database.supabase_integration.config import DictSource, SettingsLoader, SupabaseSettings
from src.database.supabase_integration.contracts.secret import Secret
from src.database.supabase_integration.contracts.settings import ConnectionSettings

SECRET = "sb_secret_PLANTED0123456789abcdef"
PUBLISHABLE = "sb_publishable_PLANTED9876543210zyxwvu"
URL = "https://projetoplantado.supabase.co"


def loaded() -> SupabaseSettings:
    return SettingsLoader().load(DictSource({
        "SBX_URL": URL, "SBX_SECRET_KEY": SECRET, "SBX_PUBLISHABLE_KEY": PUBLISHABLE,
        "SBX_BUCKET_DEFAULT": "docs", "SBX_TABLES_ALLOWLIST": "clientes",
    }))


def test_compoe_as_cinco_fatias():
    s = loaded()
    assert {f.name for f in dataclasses.fields(s)} == {"connection", "tables", "storage", "logging", "environment"}
    assert s.connection.url == URL and s.connection.secret_key.reveal() == SECRET
    assert s.storage.default_bucket == "docs" and s.tables.allowlist == ("clientes",)


def test_defaults_permitem_construir_sem_loader():
    s = SupabaseSettings()
    assert s.environment.env == "dev" and s.connection.url == ""


def test_imutavel_raiz_e_fatias():
    s = loaded()
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.connection = ConnectionSettings()  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.connection.url = "outra"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.logging.level = "ERROR"  # type: ignore[misc]
    with pytest.raises(AttributeError):
        s.connection.secret_key._value = "x"  # type: ignore[misc]


def test_repr_e_str_sem_segredo_nem_url():
    s = loaded()
    for text in (repr(s), str(s), repr(s.connection), f"{s}", f"{s.connection!s}"):
        for planted in (SECRET, PUBLISHABLE):
            assert planted not in text
    assert URL not in repr(s) and URL not in str(s)
    assert "SupabaseSettings(" in repr(s) and "***" in repr(s)


def test_safe_summary_so_nomes_e_estado():
    s = loaded()
    summary = s.safe_summary()
    assert summary["env"] == "dev"
    assert summary["connection"]["secret_key"] == "definido"
    assert summary["connection"]["url"] == "definido"
    assert summary["storage"]["default_bucket"] == "definido"
    assert summary["storage"]["allowed_mime"] == "não definido"
    assert summary["environment"]["expected_project_ref"] == "não definido"
    text = repr(summary)
    for planted in (SECRET, PUBLISHABLE, URL, "docs", "clientes"):
        assert planted not in text


def test_safe_summary_segredo_vazio_nao_definido():
    s = SupabaseSettings(connection=ConnectionSettings(url="", secret_key=Secret("")))
    assert s.safe_summary()["connection"]["secret_key"] == "não definido"
    assert s.safe_summary()["connection"]["url"] == "não definido"


def test_nao_serializavel_por_pickle_por_causa_do_secret():
    with pytest.raises(TypeError):
        pickle.dumps(loaded())
