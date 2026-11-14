"""Integração Supabase (independente do restante do projeto). Ver ``supabase/README.md``.

Uso rápido::

    from bai_supabase import create_integration_from_env, TableDescriptor
    sb = create_integration_from_env(descriptors=[TableDescriptor("clientes")])
    sb.tables.table("clientes").insert({"nome": "Ana"})
"""

from bai_supabase.contracts import (  # noqa: F401
    Condition,
    FilterGroup,
    Op,
    PageRequest,
    Query,
    Sort,
    TableDescriptor,
    UploadOptions,
)
from bai_supabase.contracts.storage import BytesSource, CollisionPolicy, PathSource, StreamSource  # noqa: F401
from bai_supabase.factories import (  # noqa: F401
    create_async_integration,
    create_integration,
    create_integration_from_env,
)
