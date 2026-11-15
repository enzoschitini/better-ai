# Plano técnico

> Traduz a [spec](spec.md) em arquitetura, respeitando a [constituição](constitution.md) e as [decisões](decisions.md). Detalhes e justificativas ficam em [research/](research/). Nomes de classes são provisórios até a Fase 0. **As assinaturas abaixo são pseudo-assinaturas de contrato, não código.**

## 1. Stack
- Python 3.12, `uv`. SDK oficial `supabase-py` (D-01), **só dentro de `adapters/`**.
- Contratos síncronos + wrapper assíncrono por thread (D-02).
- Biblioteca padrão para configuração e logs (A-12). `filetype` para detectar tipo e um cliente TUS para uploads resumable (A-06, A-07), ambos confirmados na Fase 0.
- Testes: `pytest` no grupo `dev` (D-08), `pytest-socket` para bloquear rede nos testes offline ([research/04](research/04-estrategia-de-testes.md)).

## 2. Estrutura de pastas

```
supabase/
├── spec/                       # esta especificação (SDD)
├── bai_supabase/               # pacote de código (sem __init__.py na pasta supabase/)
│   ├── config/                 # SupabaseSettings, SettingsSource, SettingsLoader
│   ├── errors/                 # hierarquia de exceções + mapeador (função pura)
│   ├── logging/                # contrato de logger, logger colorido, sanitizador
│   ├── resilience/             # políticas (timeout, retry) e executor
│   ├── contracts/              # interfaces: tabelas, arquivos, adapters, logger
│   ├── tables/                 # classe de tabelas, descritor, Query Object, Page, lote
│   ├── storage/                # classe de arquivos, validadores, nomeação, colisão
│   ├── adapters/               # único lugar que importa o SDK
│   ├── facade/                 # classe integradora + resultados compostos
│   └── factories/              # monta tudo a partir de SupabaseSettings
├── tests/                      # unit, contract, integration, e2e, fakes, support
├── .env.example                # só nomes das variáveis (versionado)
├── .env.test.example           # só nomes das variáveis de teste
└── pytest.ini                  # pythonpath = .
```

Regras de dependência entre módulos (verificadas por teste de arquitetura):
- `contracts/` e `errors/` não dependem de nenhum outro módulo.
- `tables/` e `storage/` dependem só de `contracts/`, `errors/` e do logger injetado. **Não importam um ao outro.**
- `adapters/` é o único que importa o SDK/`httpx`.
- `facade/` depende só de `contracts/` e `errors/`.
- Só `factories/` conhece implementações concretas.

## 3. Componentes e contratos

### 3.1 Configuração ([research/03](research/03-configuracao-centralizada.md))
`SupabaseSettings` imutável, em fatias (conexão, tabelas, arquivos, log, ambiente); `SettingsSource` (`EnvironmentSource`, `DotenvFileSource`, `DictSource`); `SettingsLoader.load(source)` valida tudo e levanta um `SettingsError` agregando **nomes** ausentes e inválidos. Segredos mascarados em `repr`. Cada classe recebe só a sua fatia.

### 3.2 Erros e resiliência ([research/02](research/02-tratamento-de-erros-e-resiliencia.md))
- Hierarquia com raiz `SupabaseIntegrationError`; atributos comuns: `message`, `operation`, `resource`, `retryable`, `status`, `provider_code`, `attempts`, `correlation_id`, `outcome_unknown`, `__cause__`.
- **Mapeador** (função pura): erro bruto normalizado → exceção do domínio, em tabelas por origem (tabelas, storage, transporte).
- **Executor de resiliência:** aplica timeout por tentativa, retry com backoff exponencial e jitter (relógio e aleatório injetáveis), `retry_budget` total e respeito a `Retry-After`. Cada método declara sua **idempotência**; só repete idempotente + `retryable`. Ponto de extensão para circuit breaker (fora da v1).

### 3.3 Logs ([constituição P7](constitution.md), [research/02](research/02-tratamento-de-erros-e-resiliencia.md) §10)
`LoggerContract` injetado. Implementação padrão com níveis, cor por nível (desligada fora de TTY/`NO_COLOR`), formatos `pretty` e `json`, campos estruturados, truncamento de valores longos e **sanitizador** único aplicado antes de qualquer log ou exceção. Registra cada erro uma vez, na fronteira que o trata.

### 3.4 Frente A: tabelas ([research/06](research/06-modelagem-de-dados.md), [research/09](research/09-lote-e-paginacao.md))

```
TableRepository[E, K]            # contrato genérico
  get_by_id(id) -> E             # RecordNotFoundError se não existe
  find(query: Query) -> list[E]  # vazia se não houver
  list(query: Query, page: PageRequest) -> Page[E]
  iterate(query) -> Iterator[E]  # varredura preguiçosa
  insert(entity) -> E            # não idempotente: sem retry
  insert_many(entities, options) -> BatchResult
  update(id, changes) -> E       # RecordNotFoundError se não existe
  update_where(filter, changes) -> int   # recusa filtro vazio
  upsert(entity | entities, on_conflict) -> E | BatchResult
  delete(id) -> DeleteResult(removed: bool)
  delete_where(filter) -> int    # recusa filtro vazio
TableDescriptor                  # nome, schema, PK, modelo opcional, colunas gerenciadas pelo servidor, chave de ordenação
Query                            # Filter (árvore), Sort, Select; operadores v1; traduzido para PostgREST no adapter
Page[E]                          # itens, próximo cursor, total opcional
BatchResult / ItemOutcome        # sucesso/falha por item, modos stop/continue
```

Adicionar uma tabela = registrar um novo `TableDescriptor`, sem editar código existente. Allowlist de tabelas e colunas validada antes de qualquer chamada.

### 3.5 Frente B: arquivos ([research/07](research/07-arquivos-grandes-e-storage.md))

```
FileStore                        # contrato
  upload(source, bucket, options) -> StoredFile(bucket, path, size, content_type, ...)
  download(bucket, path) -> bytes | stream | grava em arquivo
  signed_url(bucket, path, ttl) -> str   # TTL limitado ao teto configurado
  public_url(bucket, path) -> str
  list(bucket, prefix, page) -> Page[ObjectInfo]
  delete(bucket, paths | prefix) -> DeleteReport
  exists(bucket, path) -> bool
FileSource                       # caminho | bytes | stream (reiniciável ou não)
NamingStrategy                   # injetável: data + UUID por padrão
CollisionPolicy                  # reject (padrão) | version | overwrite
Validators                       # tamanho, extensão, MIME, magic bytes, sanitização de caminho
UploadTransport                  # padrão | resumable (TUS), escolhido pelo tamanho
```

### 3.6 Fachada ([research/08](research/08-consistencia-entre-frentes.md))

```
SupabaseIntegration
  tables: TableRepository          # delegação, sem lógica própria
  storage: FileStore               # delegação, sem lógica própria
  save_file_with_record(file, record_spec) -> CompositeResult
  replace_file_in_record(...)      -> CompositeResult   # caminho novo + apaga o antigo depois
  delete_record_and_file(...)      -> CompositeResult   # registro primeiro, arquivo depois
CompositeResult: status ∈ {completa, parcial, falhou}, passos concluídos, orfao_possivel, correlation_id
```
Ordem fixa e compensação de melhor esforço (decisão C-1). A fachada não captura nem traduz exceções das duas classes.

### 3.7 Adapters e Factory
`adapters/` implementa os contratos de transporte sobre o SDK (cliente síncrono) e converte qualquer exceção em **erro bruto normalizado**. `factories/create_integration(settings, *, overrides)` valida a configuração, cria logger, executor, adapters, as duas classes e a fachada; aceita substituições (fakes) para teste. Também há `AsyncIntegration`, um wrapper fino por thread (D-02).

## 4. Visão das três classes e fluxo de uma chamada

```
            ┌─────────────────────┐
 backend ──▶│  SupabaseIntegration │  (fachada única)
            └──────────┬──────────┘
              compõe   │   compõe
            ┌──────────┴──────────┐
            ▼                     ▼
   ┌────────────────┐   ┌────────────────┐
   │ Classe tabelas │   │ Classe arquivos│   (não se conhecem)
   └───────┬────────┘   └───────┬────────┘
           ▼                    ▼
        executor de resiliência → adapter → SDK Supabase
```

```
backend → SupabaseIntegration → TableRepository | FileStore
        → [executor: timeout + retry] → adapter → SDK
                                             ↓ exceção do SDK
                                    erro bruto normalizado → mapeador → exceção do domínio
```

## 5. Estratégia de testes ([research/04](research/04-estrategia-de-testes.md))
- **Unitários** com fakes por injeção e rede bloqueada. **Contrato:** a mesma bateria roda no fake e no adapter real. **Integração:** só em projeto de teste ou stack local, com `env_guard`, prefixos por execução e limpeza. **E2E:** fluxos pela fachada.
- Testes de arquitetura (isolamento do SDK, independência da integração antiga, sem leitura de ambiente fora do módulo de fonte), do mapeamento de erros, do retry com relógio falso e do **segredo plantado**.
- Cobertura mínima: 90% de linhas e 80% de ramos nos testes offline.

## 6. Rastreabilidade

| Requisito | Componente | Pesquisa |
|---|---|---|
| FR-A1…A10 | `tables/`, `adapters/` | 06, 09 |
| FR-B1…B8 | `storage/`, `adapters/` | 07 |
| FR-C1…C3 | `facade/`, `factories/` | 08 |
| FR-T1 | `config/` | 03 |
| FR-T2 | `errors/`, `resilience/` | 02 |
| FR-T3 | `logging/` | 02 §10, 03 |
| FR-T4 | validadores, allowlists, sanitizador | 05 |
| NFR-1…5 | testes de arquitetura, `pytest.ini`, `pyproject.toml` | 04 |

## 7. Riscos
| Risco | Mitigação |
|---|---|
| Pasta `supabase/` sombrear o SDK `supabase` | D-07: sem `__init__.py` em `supabase/`, pacote `bai_supabase`; teste de que `import supabase` devolve o SDK |
| Comportamento do SDK diferente do documentado | Contrato de adapter + bateria de contrato; confirmar exceções na versão do `uv.lock` (Fase 0) |
| Limites reais do projeto diferentes dos padrões propostos | Valores configuráveis; levantar na plataforma (D-05) |
| Fakes divergirem do comportamento real | Bateria de contrato roda nos dois |
| Operações combinadas deixarem órfãos | Compensação de melhor esforço + log `orfao_possivel`; limpeza manual na v1 |
