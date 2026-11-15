"""SupabaseClientProvider: criação preguiçosa, única, sem rede e sem vazar a chave."""
from __future__ import annotations

import threading

import httpx
import pytest

from src.database.supabase_integration.adapters.client import SupabaseClientProvider
from src.database.supabase_integration.contracts.secret import Secret
from src.database.supabase_integration.contracts.settings import ConnectionSettings
from src.database.supabase_integration.errors import ConfigurationError
from src.database.supabase_integration.tests.fakes.logger import CaptureLogger

KEY = "CHAVE-SECRETA-PLANTADA-999"


def make_settings(**kw) -> ConnectionSettings:
    base = dict(url="https://proj.supabase.co", secret_key=Secret(KEY), schema="app")
    base.update(kw)
    return ConnectionSettings(**base)


class FakeClient:
    def __init__(self, url, key, options):
        self.url, self.key, self.options = url, key, options
        self.postgrest = object()
        self.storage = object()


class Factory:
    def __init__(self):
        self.calls = []

    def __call__(self, url, key, options):
        self.calls.append((url, key, options))
        return FakeClient(url, key, options)


def test_lazy_and_single_creation():
    factory = Factory()
    provider = SupabaseClientProvider(make_settings(), client_factory=factory)
    assert factory.calls == [] and provider.created is False
    first = provider.client()
    assert provider.client() is first and provider.table_client() is first.postgrest
    assert provider.storage_client() is first.storage
    assert len(factory.calls) == 1 and provider.created is True


def test_factory_receives_secret_and_options_from_settings():
    factory = Factory()
    provider = SupabaseClientProvider(
        make_settings(http_timeout_seconds=7, connect_timeout_seconds=2),
        storage_timeout_seconds=90.2,
        client_factory=factory,
    )
    provider.client()
    url, key, options = factory.calls[0]
    assert (url, key) == ("https://proj.supabase.co", KEY)
    assert options.schema == "app"
    assert options.auto_refresh_token is False and options.persist_session is False
    timeout = options.postgrest_client_timeout
    assert isinstance(timeout, httpx.Timeout) and timeout.read == 7 and timeout.connect == 2
    assert options.storage_client_timeout == 91


def test_storage_timeout_defaults_to_http_timeout():
    factory = Factory()
    SupabaseClientProvider(make_settings(http_timeout_seconds=10), client_factory=factory).client()
    assert factory.calls[0][2].storage_client_timeout == 10


def test_thread_safe_single_creation():
    factory = Factory()
    provider = SupabaseClientProvider(make_settings(), client_factory=factory)
    barrier = threading.Barrier(8)
    seen = []

    def worker():
        barrier.wait()
        seen.append(provider.client())

    threads = [threading.Thread(target=worker) for _ in range(8)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert len(factory.calls) == 1 and len({id(c) for c in seen}) == 1


def test_secret_never_in_repr_or_logs():
    logger = CaptureLogger()
    provider = SupabaseClientProvider(make_settings(), client_factory=Factory(), logger=logger)
    provider.client()
    assert KEY not in repr(provider) and KEY not in str(provider)
    assert KEY not in repr(make_settings())
    assert all(KEY not in repr(event) for event in logger.events)
    assert logger.levels() == ["DEBUG"]


@pytest.mark.parametrize("settings", [make_settings(url=""), make_settings(secret_key=Secret(""))])
def test_missing_credentials_fail_without_values(settings):
    provider = SupabaseClientProvider(settings, client_factory=Factory())
    with pytest.raises(ConfigurationError) as info:
        provider.client()
    assert KEY not in str(info.value)


def test_factory_failure_becomes_configuration_error_keeping_cause():
    boom = RuntimeError(f"falha com {KEY}")

    def failing(url, key, options):
        raise boom

    with pytest.raises(ConfigurationError) as info:
        SupabaseClientProvider(make_settings(), client_factory=failing).client()
    assert info.value.__cause__ is boom
    assert KEY not in str(info.value)


def test_http_client_has_auth_and_is_created_once_and_closed():
    created = []

    def http_factory(**kwargs):
        client = httpx.Client(**kwargs)
        created.append(client)
        return client

    provider = SupabaseClientProvider(make_settings(), client_factory=Factory(), http_client_factory=http_factory)
    http = provider.http_client()
    assert provider.http_client() is http and len(created) == 1
    assert str(http.base_url).rstrip("/") == "https://proj.supabase.co"
    assert http.headers["apikey"] == KEY
    provider.close()
    assert http.is_closed


def test_real_sdk_client_is_created_offline_with_configured_timeouts():
    """Usa o ``create_client`` real: a criação não pode tocar a rede."""
    provider = SupabaseClientProvider(make_settings(http_timeout_seconds=9, connect_timeout_seconds=2))
    client = provider.client()
    assert provider.client() is client
    assert client.options.schema == "app"
    assert client.options.auto_refresh_token is False and client.options.persist_session is False
    assert client.postgrest is provider.table_client()
    assert provider.storage_client() is client.storage
    assert KEY not in repr(provider)
