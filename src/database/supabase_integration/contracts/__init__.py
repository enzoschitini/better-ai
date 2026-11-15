"""Contratos (interfaces) da integração. Sem dependência de outros módulos além de ``errors``."""

from bai_supabase.contracts.logging import LoggerContract  # noqa: F401
from bai_supabase.contracts.query import (  # noqa: F401
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
from bai_supabase.contracts.resilience import (  # noqa: F401
    Operation,
    ResilienceExecutor,
    RetryPolicy,
    TimeoutPolicy,
)
from bai_supabase.contracts.results import (  # noqa: F401
    BatchResult,
    CompositeResult,
    CompositeStatus,
    DeleteReport,
    DeleteResult,
    ItemOutcome,
    ObjectInfo,
    StoredFile,
)
from bai_supabase.contracts.secret import Secret  # noqa: F401
from bai_supabase.contracts.settings import (  # noqa: F401
    ConnectionSettings,
    EnvironmentSettings,
    LoggingSettings,
    StorageSettings,
    TablesSettings,
)
from bai_supabase.contracts.storage import (  # noqa: F401
    BytesSource,
    CollisionPolicy,
    FileSource,
    FileStore,
    NamingStrategy,
    PathSource,
    StreamSource,
    UploadOptions,
)
from bai_supabase.contracts.tables import (  # noqa: F401
    BatchOptions,
    TableDescriptor,
    TableRepository,
    TablesContract,
)
from bai_supabase.contracts.transports import (  # noqa: F401
    SelectRequest,
    SelectResponse,
    StorageTransport,
    TableTransport,
    TransportObject,
)
