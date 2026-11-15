"""Contratos (interfaces) da integração. Sem dependência de outros módulos além de ``errors``."""

from src.database.supabase_integration.contracts.logging import LoggerContract  # noqa: F401
from src.database.supabase_integration.contracts.query import (  # noqa: F401
    Condition,
    Filter,
    FilterGroup,
    Op,
    Page,
    PageRequest,
    Query,
    Sort,
    is_empty_filter,
)
from src.database.supabase_integration.contracts.resilience import (  # noqa: F401
    Operation,
    ResilienceExecutor,
    RetryPolicy,
    TimeoutPolicy,
)
from src.database.supabase_integration.contracts.results import (  # noqa: F401
    BatchResult,
    CompositeResult,
    CompositeStatus,
    DeleteReport,
    DeleteResult,
    ItemOutcome,
    ObjectInfo,
    StoredFile,
)
from src.database.supabase_integration.contracts.secret import Secret  # noqa: F401
from src.database.supabase_integration.contracts.settings import (  # noqa: F401
    ConnectionSettings,
    EnvironmentSettings,
    LoggingSettings,
    StorageSettings,
    TablesSettings,
)
from src.database.supabase_integration.contracts.storage import (  # noqa: F401
    BytesSource,
    CollisionPolicy,
    FileSource,
    FileStore,
    NamingStrategy,
    PathSource,
    StreamSource,
    UploadOptions,
)
from src.database.supabase_integration.contracts.tables import (  # noqa: F401
    BatchOptions,
    TableDescriptor,
    TableRepository,
    TablesContract,
)
from src.database.supabase_integration.contracts.transports import (  # noqa: F401
    SelectRequest,
    SelectResponse,
    StorageTransport,
    TableTransport,
    TransportObject,
)
