"""Factory: montagem, falha cedo e coexistência com variáveis antigas (T-402)."""
from __future__ import annotations

import pytest

from bai_supabase import TableDescriptor, create_integration_from_env
from bai_supabase.config import DictSource, SettingsLoader
from bai_supabase.errors import SettingsError
from bai_supabase.facade import AsyncSupabaseIntegration, SupabaseIntegration
from bai_supabase.factories import create_async_integration, create_integration
from tests.fakes.storage_transport import InMemoryStorageTransport
from tests.fakes.table_transport import InMemoryTableTransport

SECRET = "chave-super-secreta-xyz"
BASE = {"SBX_URL": "https://abc.supabase.co", "SBX_SECRET_KEY": SECRET, "SBX_BUCKET_DEFAULT": "docs"}


def _fakes():
    tt = InMemoryTableTransport()
    tt.configure("t")
    return tt, InMemoryStorageTransport()


def test_cria_fachada_com_fakes():
    settings = SettingsLoader().load(DictSource(BASE))
    tt, st = _fakes()
    sb = create_integration(settings, descriptors=[TableDescriptor("t")], table_transport=tt, storage_transport=st)
    assert isinstance(sb, SupabaseIntegration)
    assert sb.tables.table("t").insert({"a": 1})["a"] == 1


def test_cria_sem_fakes_nao_toca_rede():
    """Com o SDK real mas sem chamar nada, a montagem não faz requisição."""
    settings = SettingsLoader().load(DictSource(BASE))
    sb = create_integration(settings, descriptors=[TableDescriptor("t")])
    assert isinstance(sb, SupabaseIntegration)


def test_config_incompleta_falha_na_factory_citando_so_nomes():
    with pytest.raises(SettingsError) as ei:
        create_integration_from_env(source=DictSource({"SBX_URL": "https://abc.supabase.co"}))
    assert "SBX_SECRET_KEY" in str(ei.value)
    assert SECRET not in str(ei.value)


def test_coexiste_com_variaveis_antigas_supabase():
    src = DictSource({**BASE, "SUPABASE_URL": "https://antigo", "SUPABASE_SECRET_KEY": "antiga"})
    tt, st = _fakes()
    sb = create_integration_from_env(source=src, descriptors=[TableDescriptor("t")], table_transport=tt, storage_transport=st)
    assert isinstance(sb, SupabaseIntegration)


def test_async_wrapper():
    import asyncio

    settings = SettingsLoader().load(DictSource(BASE))
    tt, st = _fakes()
    asb = create_async_integration(settings, descriptors=[TableDescriptor("t")], table_transport=tt, storage_transport=st)
    assert isinstance(asb, AsyncSupabaseIntegration)

    async def go():
        repo = asb.sync.tables.table("t")
        return await asb.run(repo.insert, {"a": 2})

    assert asyncio.run(go())["a"] == 2


def test_segredo_nao_aparece_em_repr_da_fachada_nem_settings():
    settings = SettingsLoader().load(DictSource(BASE))
    assert SECRET not in repr(settings) and SECRET not in str(settings.safe_summary())


def test_regressao_factory_liga_provedor_real_ao_transporte_de_storage_e_tabelas():
    """Bug achado no smoke real: a Factory passava ``client.storage`` onde o transporte esperava o
    cliente completo. Aqui o provedor real é usado com um SDK FALSO que imita a forma do cliente."""
    from bai_supabase.adapters.client import SupabaseClientProvider

    calls = []

    class _Bucket:
        def list(self, path, options):
            calls.append(("list", path))
            return [{"name": "a.txt", "id": "x", "metadata": {"size": 3, "mimetype": "text/plain"}}]

    class _Storage:
        def from_(self, bucket):
            calls.append(("bucket", bucket))
            return _Bucket()

    class _Query:
        def select(self, *a, **k):
            return self

        def limit(self, *a, **k):
            return self

        def range(self, *a, **k):
            return self

        def order(self, *a, **k):
            return self

        def execute(self):
            class R:
                data = [{"id": 1}]
                count = 1

            return R()

    class _Postgrest:
        def from_(self, table):
            calls.append(("table", table))
            return _Query()

        def schema(self, name):
            return self

    class _Client:
        storage = _Storage()
        postgrest = _Postgrest()

    settings = SettingsLoader().load(DictSource(BASE))
    provider = SupabaseClientProvider(settings.connection, client_factory=lambda *a, **k: _Client())
    sb = create_integration(settings, descriptors=[TableDescriptor("t")], client_provider=provider)

    page = sb.storage.list(prefix="", limit=5)
    assert [o.name for o in page.items] == ["a.txt"]
    assert ("bucket", "docs") in calls
    assert sb.tables.table("t").list().items == [{"id": 1}]
    assert ("table", "t") in calls
