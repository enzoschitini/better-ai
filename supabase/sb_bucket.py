import sys; sys.path.insert(0, "supabase")   # só se não rodar de dentro de supabase/

from bai_supabase import (
    create_integration_from_env, TableDescriptor,
    Query, Condition, Op, PageRequest, Sort,
    BytesSource, PathSource, UploadOptions, CollisionPolicy,
)
from bai_supabase.contracts import FilterGroup, BatchOptions
from bai_supabase.errors import RecordNotFoundError, FileAlreadyExistsError, SupabaseIntegrationError

# Lê SBX_* do ambiente + .env (só em dev). Falha cedo, listando só os NOMES que faltam.
sb = create_integration_from_env(
    dotenv_path=".env",
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

# UPLOAD (escolhe padrão ou resumable pelo tamanho; valida tamanho, extensão, MIME e conteúdo)
st = sb.storage.upload(
    BytesSource(b"conteudo", filename="nota.txt", content_type="text/plain"),
    UploadOptions(folder="docs"),                        # caminho gerado: docs/AAAA/MM/<uuid>.txt
)
print(st.bucket, st.path, st.size, st.upload_mode)

# python supabase/sb_bucket.py