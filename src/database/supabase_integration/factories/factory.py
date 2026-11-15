"""Factory: único lugar que conhece as implementações concretas (plano §2).

Recebe ``SupabaseSettings`` já validadas, monta logger, executor, adapters, as duas classes
e a fachada. Aceita substituições (fakes) para teste. NÃO lê o ambiente; para isso use
``create_integration_from_env`` (ponto de composição).
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Union

from src.database.supabase_integration.adapters.client import SupabaseClientProvider
from src.database.supabase_integration.adapters.storage_transport import SupabaseStorageTransport
from src.database.supabase_integration.adapters.tables_transport import SupabaseTableTransport
from src.database.supabase_integration.adapters.tus import TusClient
from src.database.supabase_integration.config.loader import SettingsLoader
from src.database.supabase_integration.config.settings import SupabaseSettings
from src.database.supabase_integration.config.sources import ChainedSource, DotenvFileSource, EnvironmentSource, SettingsSource
from src.database.supabase_integration.contracts.logging import LoggerContract
from src.database.supabase_integration.contracts.resilience import ResilienceExecutor
from src.database.supabase_integration.contracts.storage import NamingStrategy
from src.database.supabase_integration.contracts.tables import TableDescriptor
from src.database.supabase_integration.contracts.transports import StorageTransport, TableTransport
from src.database.supabase_integration.facade.async_wrapper import AsyncSupabaseIntegration
from src.database.supabase_integration.facade.integration import SupabaseIntegration
from src.database.supabase_integration.logging.logger import build_logger
from src.database.supabase_integration.resilience.executor import build_executor
from src.database.supabase_integration.storage.service import SupabaseStorage
from src.database.supabase_integration.tables.service import SupabaseTables


def create_integration(
    settings: SupabaseSettings,
    *,
    descriptors: Iterable[TableDescriptor] = (),
    logger: Optional[LoggerContract] = None,
    executor: Optional[ResilienceExecutor] = None,
    table_transport: Optional[TableTransport] = None,
    storage_transport: Optional[StorageTransport] = None,
    naming: Optional[NamingStrategy] = None,
    client_provider: Optional[SupabaseClientProvider] = None,
) -> SupabaseIntegration:
    """Monta a fachada. Qualquer dependência pode ser substituída (fakes/testes)."""
    log = logger or build_logger(settings.logging, extra_secrets=[settings.connection.secret_key])
    exe = executor or build_executor(settings.connection, log)

    provider = client_provider
    if provider is None and (table_transport is None or storage_transport is None):
        provider = SupabaseClientProvider(
            settings.connection,
            storage_timeout_seconds=settings.storage.upload_timeout_seconds,
            logger=log,
        )

    if table_transport is None:
        table_transport = SupabaseTableTransport(provider.table_client, default_schema=settings.connection.schema)

    if storage_transport is None:
        tus = TusClient(
            settings.connection.url,
            settings.connection.secret_key.reveal,
            logger=log,
        )
        storage_transport = SupabaseStorageTransport(provider.client, resumable=tus)  # espera o cliente completo (faz .storage.from_)

    tables = SupabaseTables(table_transport, exe, log, settings.tables, descriptors=descriptors)
    storage = SupabaseStorage(
        transport=storage_transport,
        executor=exe,
        logger=log,
        settings=settings.storage,
        naming=naming,
    )
    log.debug("integração montada", env=settings.environment.env, summary=settings.safe_summary())
    return SupabaseIntegration(tables, storage, log)


def create_async_integration(
    settings: SupabaseSettings, **kwargs
) -> AsyncSupabaseIntegration:
    """Mesma montagem, com o wrapper assíncrono por thread (decisão D-02)."""
    integration = create_integration(settings, **kwargs)
    return AsyncSupabaseIntegration(integration, max_concurrency=settings.storage.max_concurrent_transfers)


def create_integration_from_env(
    *,
    dotenv_path: Union[str, Path, None] = None,
    source: Optional[SettingsSource] = None,
    descriptors: Iterable[TableDescriptor] = (),
    **kwargs,
) -> SupabaseIntegration:
    """Ponto de composição: lê o ambiente do processo (e, só em dev, um arquivo ``.env``),
    valida e monta. ``SettingsError`` lista só NOMES de variáveis ausentes/inválidas."""
    if source is None:
        sources: list[SettingsSource] = [EnvironmentSource()]
        if dotenv_path is not None:
            sources.append(DotenvFileSource(dotenv_path))
        source = ChainedSource(*sources)
    settings = SettingsLoader().load(source)
    return create_integration(settings, descriptors=descriptors, **kwargs)
