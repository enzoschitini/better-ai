import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))   # pasta supabase/ (onde está bai_supabase)

from bai_supabase import (
    create_integration_from_env, TableDescriptor,
    Query, Condition, Op, PageRequest, Sort,
    BytesSource, PathSource, UploadOptions, CollisionPolicy,
)
from bai_supabase.contracts import FilterGroup, BatchOptions
from bai_supabase.errors import RecordNotFoundError, FileAlreadyExistsError, SupabaseIntegrationError

# Lê SBX_* do ambiente + .env (só em dev). Falha cedo, listando só os NOMES que faltam.
sb = create_integration_from_env(
    dotenv_path=Path(__file__).resolve().parents[1] / ".env",
    descriptors=[
        TableDescriptor(
            "sbx_test_items",
            columns=("id", "name", "qty", "bucket", "path", "created_at"),  # allowlist de colunas
            server_managed_columns=("id", "created_at"),                    # o servidor preenche
            sort_key="created_at",                                          # habilita keyset
        )
    ],
)
items = sb.tables.table("sbx_test_items")

achados = items.find(Query.where(Condition("name", Op.ILIKE, "an%")))   # [] se nada
q = Query(
    filter=FilterGroup(items=(
        Condition("qty", Op.GTE, 5),
        FilterGroup(items=(Condition("qty", Op.EQ, 7), Condition("qty", Op.EQ, 9)), logic="or"),
    )),
    sorts=(Sort("name"),),
)
pag = items.list(q, PageRequest(limit=10, offset=0, include_count=True))
print(pag.items, pag.total, pag.has_more) 

# python supabase/sb_crud.py