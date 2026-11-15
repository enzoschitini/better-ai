"""Classe de tabelas: registro de descritores e acesso a repositórios (``TablesContract``).

Open/Closed: nova tabela = novo ``TableDescriptor`` registrado; nenhum código existente muda.
Esta classe não conhece o módulo de arquivos.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable, Optional

from src.database.supabase_integration.contracts.logging import LoggerContract
from src.database.supabase_integration.contracts.resilience import ResilienceExecutor
from src.database.supabase_integration.contracts.settings import TablesSettings
from src.database.supabase_integration.contracts.tables import TableDescriptor, TableRepository
from src.database.supabase_integration.contracts.transports import TableTransport
from src.database.supabase_integration.errors.exceptions import ConfigurationError
from src.database.supabase_integration.tables.repository import PostgresTableRepository
from src.database.supabase_integration.tables.validation import ensure_table_allowed, safe_name, validate_descriptor

RepositoryFactory = Callable[[TableDescriptor], TableRepository]


class SupabaseTables:
    """Registro de descritores; entrega um repositório por tabela registrada e permitida."""

    def __init__(
        self,
        transport: TableTransport,
        executor: ResilienceExecutor,
        logger: LoggerContract,
        settings: TablesSettings,
        *,
        descriptors: Iterable[TableDescriptor] = (),
        repository_factory: Optional[RepositoryFactory] = None,
    ) -> None:
        self._settings = settings
        self._log = logger.bind(component="tables")
        self._factory: RepositoryFactory = repository_factory or (
            lambda d: PostgresTableRepository(d, transport, executor, logger, settings)
        )
        self._descriptors: dict[str, TableDescriptor] = {}
        self._repositories: dict[str, TableRepository] = {}
        for descriptor in descriptors:
            self.register(descriptor)

    def register(self, descriptor: TableDescriptor) -> None:
        """Registra um descritor. Repetir o mesmo é no-op; outro com o mesmo nome é erro."""
        validate_descriptor(descriptor, self._settings.allowlist)
        existing = self._descriptors.get(descriptor.name)
        if existing is not None:
            if existing == descriptor:
                return
            raise ConfigurationError(
                f"tabela já registrada com outro descritor: {safe_name(descriptor.name)}", resource=descriptor.name
            )
        self._descriptors[descriptor.name] = descriptor
        self._log.debug("tabela registrada", table=descriptor.name, schema=descriptor.schema)

    def table(self, name: str) -> TableRepository[Any, Any]:
        """``ConfigurationError`` se a tabela não estiver permitida ou registrada."""
        ensure_table_allowed(name, self._settings.allowlist)
        descriptor = self._descriptors.get(name)
        if descriptor is None:
            raise ConfigurationError(f"tabela não registrada: {safe_name(name)}")
        repository = self._repositories.get(name)
        if repository is None:
            repository = self._repositories[name] = self._factory(descriptor)
        return repository

    def registered(self) -> tuple[str, ...]:
        """Nomes das tabelas registradas (ordem de registro)."""
        return tuple(self._descriptors)
