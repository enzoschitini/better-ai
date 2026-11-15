# rode da raiz do repo: python -m src.database.supabase_integration.examples.sb_bucket

from src.database.supabase_integration import (
    create_integration_from_env, TableDescriptor,
    Query, Condition, Op, PageRequest, Sort,
    BytesSource, PathSource, UploadOptions, CollisionPolicy,
)
from src.database.supabase_integration.contracts import FilterGroup, BatchOptions
from src.database.supabase_integration.errors import RecordNotFoundError, FileAlreadyExistsError, SupabaseIntegrationError

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

# python -m src.database.supabase_integration.examples.sb_bucket