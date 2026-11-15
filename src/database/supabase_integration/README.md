# Integração Supabase (`src/database/supabase_integration/`)

Integração do backend com o Supabase: CRUD de tabelas, arquivos em buckets e uma fachada única que combina as duas. O pacote é autocontido: não importa nenhum outro código de `src/` (garantido pelo teste de arquitetura). É a **única** integração com o Supabase do projeto; fluxos de arquivo e tabela devem usá-la.

- **Guia de uso completo (receitas, arquitetura e referência): [GUIA_DE_USO.md](docs/GUIA_DE_USO.md)**
- Especificação (SDD): [spec/](docs/spec/README.md) · decisões: [spec/decisions.md](docs/spec/decisions.md) · tarefas: [spec/tasks.md](docs/spec/tasks.md)
- Testes: [tests/](tests/) · exemplos executáveis: [examples/](examples/)

## Estrutura

```
src/database/supabase_integration/
├── config/ errors/ logging/ resilience/ contracts/ tables/ storage/ adapters/ facade/ factories/
│   (config: SupabaseSettings/loader · adapters: ÚNICO lugar que importa o SDK · facade: fachada + lote/compensação)
├── tests/               # unit, contract, architecture, integration (live), e2e, fakes, support
├── examples/            # sb_crud.py, sb_bucket.py (python -m src.database.supabase_integration.examples.sb_crud)
├── docs/                # GUIA_DE_USO.md e spec/ (SDD)
├── .env.example         # nomes das variáveis (sem valores)
├── .env.test.example    # nomes das variáveis de teste live (sem valores)
└── pytest.ini
```

## Como testar

Todos os comandos são executados **a partir da raiz do repositório** (`better-ai/`), com o ambiente virtual do projeto (`.venv`). Os testes offline **bloqueiam a rede** e não precisam de credenciais.

> No PowerShell: `.venv\Scripts\python.exe -m pytest ...` · No Git Bash: `.venv/Scripts/python.exe -m pytest ...` · Com o venv ativado: `python -m pytest ...`

### 1. Primeiro teste (rápido, offline)

```bash
python -m pytest src/database/supabase_integration/tests -m "not integration" -q
```

Resultado esperado: **725 passed** (os 3 testes live ficam de fora).

### 2. Por área

| O que validar | Comando | Esperado |
|---|---|---|
| **Tudo offline** | `python -m pytest src/database/supabase_integration/tests -m "not integration" -q` | 725 passed |
| **Arquitetura** (SDK só em `adapters/`, independência, sem sombrear o SDK `supabase`) | `python -m pytest src/database/supabase_integration/tests/architecture -q` | 10 passed |
| **Configuração** | `python -m pytest src/database/supabase_integration/tests/unit/test_config_loader.py src/database/supabase_integration/tests/unit/test_config_sources.py src/database/supabase_integration/tests/unit/test_config_settings.py -q` | passed |
| **Logs e sanitizador** (segredo plantado, cores, JSON) | `python -m pytest src/database/supabase_integration/tests/unit/test_logger.py src/database/supabase_integration/tests/unit/test_sanitizer.py -q` | passed |
| **Erros** (mapeador e normalização do SDK) | `python -m pytest src/database/supabase_integration/tests/unit/test_error_mapper.py src/database/supabase_integration/tests/unit/test_normalize.py -q` | passed |
| **Resiliência** (retry, backoff, orçamento) | `python -m pytest src/database/supabase_integration/tests/unit/test_resilience.py -q` | passed |
| **Frente A: tabelas** | `python -m pytest src/database/supabase_integration/tests/unit/test_tables_*.py src/database/supabase_integration/tests/contract/test_table_repository_contract.py -q` | passed |
| **Frente B: arquivos** | `python -m pytest src/database/supabase_integration/tests/unit/test_storage_*.py src/database/supabase_integration/tests/unit/test_tus.py src/database/supabase_integration/tests/contract/test_file_store_contract.py -q` | passed |
| **Fachada** (operações combinadas, compensação) | `python -m pytest src/database/supabase_integration/tests/unit/test_facade.py -q` | 11 passed |
| **Factory** | `python -m pytest src/database/supabase_integration/tests/unit/test_factory.py -q` | 6 passed |
| **Contrato** (mesma bateria para fake e, futuramente, adapter real) | `python -m pytest src/database/supabase_integration/tests/contract -q` | 34 passed |

Dicas: `-x` para parar no primeiro erro · `-k nome` para filtrar · `-W ignore` silencia avisos de terceiros · `-s` mostra os logs coloridos durante o teste.

### 3. Testes LIVE (contra um projeto Supabase de teste)

Só rodam com consentimento explícito e **nunca** devem apontar para produção ou homologação.

1. Crie um projeto Supabase **dedicado a testes**.
2. No SQL Editor, rode [tests/support/test_schema.sql](tests/support/test_schema.sql) (a integração não faz DDL).
3. No Storage, crie um bucket **privado** (ex.: `it-bucket`).
4. Copie `src/database/supabase_integration/.env.test.example` para `src/database/supabase_integration/.env.test` (ignorado pelo Git) e preencha:
   `SBX_TEST_URL`, `SBX_TEST_SECRET_KEY`, `SBX_TEST_BUCKET`, `SBX_TEST_PROJECT_REF` e `SBX_TEST_ALLOW_LIVE=1`.
   (Para obter URL, chave e nomes seguindo o guia de leitura da plataforma, veja [spec/research/01-variaveis-de-ambiente.md](docs/spec/research/01-variaveis-de-ambiente.md).)
5. Rode:

```bash
python -m pytest src/database/supabase_integration/tests/integration -m integration -v -s
```

Sem as variáveis, os 3 testes são **pulados** (não falham). Eles criam dados com prefixo `it-<id>` e limpam ao final.

## Como usar (resumo)

```python
from src.database.supabase_integration import (
    create_integration_from_env, TableDescriptor, BytesSource, UploadOptions, Query, Condition, Op,
)

# lê SBX_* do ambiente (e, em dev, de um .env); falha cedo listando só NOMES ausentes
sb = create_integration_from_env(
    dotenv_path=".env",  # só em dev
    descriptors=[TableDescriptor("clientes")],
)

# tabelas
clientes = sb.tables.table("clientes")
novo = clientes.insert({"nome": "Ana"})
clientes.find(Query.where(Condition("nome", Op.ILIKE, "an%")))

# arquivos
stored = sb.storage.upload(BytesSource(b"...", filename="nota.txt", content_type="text/plain"), UploadOptions(folder="fotos"))
url = sb.storage.signed_url(stored.path, ttl_seconds=300)

# arquivo + registro (compensa em caso de falha; devolve completa/parcial/falhou)
r = sb.save_file_with_record("clientes", BytesSource(b"..."), lambda s: {"nome": "Ana", "bucket": s.bucket, "path": s.path})
r.raise_if_failed()
```

Em FastAPI use `create_async_integration(settings)` (executa em threads, sem bloquear o event loop).

## Variáveis de ambiente

Lista completa e comentada em [.env.example](.env.example). Mínimo: `SBX_URL`, `SBX_SECRET_KEY` e `SBX_BUCKET_DEFAULT` (se usar arquivos). Os nomes `SBX_*` são **independentes** dos `SUPABASE_*` da integração antiga; as duas coexistem.

## Status e pendências

Implementado e validado **offline (726+ testes)** e **contra um projeto Supabase real de teste** (testes live: `python -m pytest src/database/supabase_integration/tests/integration -m integration`, 3 passed).

Validado no projeto real:
- **Arquivos:** upload padrão, upload resumable (TUS) de 20 MiB com checksum igual, download em stream, URL assinada, listagem, colisão (`FileAlreadyExistsError`), exclusão e limpeza.
- **Tabelas:** insert em lote, upsert, paginação por offset e por keyset sem repetição, varredura (`iterate`), filtro com grupo `or`, `update_where`, `RecordNotFoundError`, delete idempotente e recusa de filtro vazio e de coluna fora da allowlist.
- **Fachada:** operação combinada completa e **compensação automática** (arquivo apagado quando o insert falha).

Ainda **não validado**:
- Dois grupos `or` irmãos no mesmo nível (um grupo `or` dentro de `and` foi validado).
- `exists` do SDK devolve `False` também em 401/403 (esconde erro de permissão).
- Limite real de itens por remoção em lote e tamanho máximo do TUS.
- Uso do endereço direto `<projeto>.storage.supabase.co` para uploads grandes (a documentação recomenda).
- Cobertura não medida (`pytest-cov` não instalado); `uv.lock` precisa de `uv lock` por causa de `filetype` no `pyproject.toml`.

A integração com o restante do projeto é uma fase futura, com spec própria.
