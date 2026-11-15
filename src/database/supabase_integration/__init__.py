"""Integração Supabase (autocontida). Ver ``README.md`` nesta pasta.

Uso rápido::

    from src.database.supabase_integration import create_integration_from_env, TableDescriptor
    sb = create_integration_from_env(descriptors=[TableDescriptor("clientes")])
    sb.tables.table("clientes").insert({"nome": "Ana"})
"""

from src.database.supabase_integration.contracts import (  # noqa: F401
    Condition,
    FilterGroup,
    Op,
    PageRequest,
    Query,
    Sort,
    TableDescriptor,
    UploadOptions,
)
from src.database.supabase_integration.contracts.storage import BytesSource, CollisionPolicy, PathSource, StreamSource  # noqa: F401
from src.database.supabase_integration.factories import (  # noqa: F401
    create_async_integration,
    create_integration,
    create_integration_from_env,
)
