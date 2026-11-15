"""Guarda de ambiente (env_guard) para testes LIVE: só roda contra projeto de teste dedicado."""
from __future__ import annotations

import uuid

import pytest

from src.database.supabase_integration import TableDescriptor, create_integration
from src.database.supabase_integration.config import DictSource, EnvironmentSource, SettingsLoader, DotenvFileSource, ChainedSource
from pathlib import Path

ENV_TEST = Path(__file__).resolve().parents[2] / ".env.test"


def _src():
    parts = [EnvironmentSource()]
    if ENV_TEST.exists():
        parts.append(DotenvFileSource(ENV_TEST))
    return ChainedSource(*parts)


@pytest.fixture(scope="session")
def live_settings():
    src = _src()
    if src.get("SBX_TEST_ALLOW_LIVE") != "1":
        pytest.skip("integração live desligada (defina SBX_TEST_ALLOW_LIVE=1 e as SBX_TEST_*)")
    url, key, bucket = src.get("SBX_TEST_URL"), src.get("SBX_TEST_SECRET_KEY"), src.get("SBX_TEST_BUCKET")
    missing = [n for n, v in (("SBX_TEST_URL", url), ("SBX_TEST_SECRET_KEY", key), ("SBX_TEST_BUCKET", bucket)) if not v]
    if missing:
        pytest.skip(f"faltam variáveis de teste: {', '.join(missing)}")
    ref = src.get("SBX_TEST_PROJECT_REF")
    if ref and ref not in url:
        pytest.fail("SBX_TEST_URL não corresponde ao SBX_TEST_PROJECT_REF (guarda de ambiente)")
    if not ref:
        pytest.skip("defina SBX_TEST_PROJECT_REF (guarda contra apontar para o projeto errado)")
    return SettingsLoader().load(
        DictSource(
            {
                "SBX_URL": url,
                "SBX_SECRET_KEY": key,
                "SBX_BUCKET_DEFAULT": bucket,
                "SBX_BUCKETS_ALLOWLIST": bucket,
                "SBX_TABLES_ALLOWLIST": "sbx_test_items",
                "SBX_ENV": "dev",
                "SBX_LOG_LEVEL": "DEBUG",
            }
        )
    )


@pytest.fixture(scope="session")
def live(live_settings):
    return create_integration(live_settings, descriptors=[TableDescriptor("sbx_test_items", columns=("id", "name", "qty", "bucket", "path", "created_at"), server_managed_columns=("id", "created_at"))])


@pytest.fixture
def run_id():
    return f"it-{uuid.uuid4().hex[:8]}"
