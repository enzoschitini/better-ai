# Estratégia de testes da integração Supabase

> **Material de pesquisa (refinamento técnico).** A visão geral citada aqui como "00" / "visão geral" agora vive em [../spec.md](../spec.md). As "Questões em aberto" deste arquivo estão **consolidadas e resolvidas em [../decisions.md](../decisions.md)**, que prevalece em caso de divergência. Tarefas de implementação: [../tasks.md](../tasks.md).

> Status: **rascunho de planejamento** (nenhum código escrito). Itens marcados como **[PROPOSTA]** são sugestões a validar; decisões pendentes estão em **Questões em aberto** (seção 14).
> Documentos relacionados: [spec.md](../spec.md) e [01-variaveis-de-ambiente.md](01-variaveis-de-ambiente.md).

## 1. Contexto e objetivo

A integração nova é composta por três classes (tabelas, arquivos e integradora/fachada), criadas por uma Factory, com SDK isolado por Adapter, logger injetado e erros de domínio próprios. Tudo vive em `supabase/`, desacoplado do código existente.

O repositório **não tem suíte pytest padrão** (o `CLAUDE.md` descreve testes como scripts ad-hoc, rodados com `python -m ...`). Portanto a escolha do framework faz parte deste planejamento, e a suíte da integração nova nasce **dentro de `supabase/`**, sem depender de conftest, fixtures ou scripts do restante do projeto.

Objetivos dos testes:

1. Provar que cada classe cumpre seu contrato, **sem tocar no Supabase real** (unitários, rápidos, rodam sempre).
2. Provar que o Adapter conversa corretamente com o Supabase de verdade (integração, **só contra projeto de teste dedicado**).
3. Garantir que logs e mapeamento de erros se comportam como especificado.
4. Garantir que nenhum segredo vaza em log, mensagem de erro ou relatório de teste.

## 2. Pirâmide de testes

```
          /\
         /E2E\          poucos: fluxo completo via fachada (integradora) no projeto de teste
        /------\
       /Integr. \       moderados: Adapter real x Supabase de teste (tabelas e storage)
      /----------\
     / Contrato   \     fakes e adapter real passam pela MESMA bateria de testes de contrato
    /--------------\
   /   Unitários    \   muitos: classes, factory, config, logger, mapeamento de erros (sem rede)
  /------------------\
```

| Camada | Alvo | Rede? | Roda quando |
|---|---|---|---|
| **Unitário** | Classe de tabelas, classe de arquivos, integradora, factory, config, logger, mapeador de erros, validações | Não | Sempre (local e CI) |
| **Contrato** | Mesma bateria de comportamento aplicada ao **fake em memória** e ao **adapter real** | Só no real | Fake: sempre. Real: com credenciais |
| **Integração** | Adapter real contra Supabase de teste (CRUD, upload/download/delete, URLs, erros reais) | Sim | Sob demanda e em CI com segredo de teste |
| **E2E (fachada)** | Cenários completos pela classe integradora com a Factory de produção | Sim | Sob demanda, poucos cenários |

Proporção alvo **[PROPOSTA]**: cerca de 70% unitários/contrato-com-fake, 25% integração, 5% E2E.

### Por que a camada de "contrato"

Como o projeto segue Liskov e DI, o fake em memória e o adapter real devem ser intercambiáveis. Uma bateria de testes de contrato **parametrizada** (rodando contra `[fake, real]`) garante que o fake não "mente" em relação ao real, o que mantém os unitários confiáveis. Se um teste de contrato passar no fake e falhar no real, o fake está errado (ou o contrato está ambíguo).

## 3. Escolha do framework

### Recomendação **[PROPOSTA]**: `pytest`

| Critério | `pytest` | `unittest` (stdlib) | Scripts ad-hoc (padrão atual do repo) |
|---|---|---|---|
| Fixtures com escopo e teardown | Excelente (`yield`, escopos) | Limitado (`setUp`/`tearDown`) | Manual |
| Parametrização (fake x real) | Nativa | Verbosa (`subTest`) | Manual |
| Marcadores e skip condicional | Nativos (`markers`, `skipif`) | `skipUnless`, sem marcadores | Não há |
| Captura de logs (`caplog`) e saída (`capsys`) | Nativa | Parcial (`assertLogs`) | Não há |
| Cobertura (`pytest-cov`) | Integrada | Possível | Difícil |
| Dependência extra | Sim (grupo dev) | Nenhuma | Nenhuma |

Justificativa: o requisito de **pular testes de rede quando faltam variáveis**, **parametrizar contra fake e real** e **limpar recursos no teardown** é exatamente o que fixtures e marcadores do pytest resolvem com pouco código. O custo (uma dependência de desenvolvimento) é baixo. Isso **não conflita** com o repositório: a suíte nova é isolada em `supabase/tests/` e não exige que o restante do projeto adote pytest.

### Dependências via `uv` **[PROPOSTA]**

Adicionar um **grupo de dependências de desenvolvimento** em `pyproject.toml` (a pasta `supabase/` não tem seu próprio `pyproject`; ver questão 3 sobre o assunto):

| Pacote | Uso |
|---|---|
| `pytest` | Runner e fixtures |
| `pytest-cov` | Cobertura |
| `pytest-asyncio` | **Somente** se a decisão sobre async (questão 2 do doc 00) for assíncrona |
| `pytest-socket` | Bloquear acesso à rede nos testes unitários (garantia de que "unitário não toca a rede") |
| `python-dotenv` | Carregar `.env.test` nos testes de integração (se não for carregado pela própria config) |
| `respx` ou `responses` | **Opcional**: simular HTTP ao testar o Adapter sem rede, conforme o cliente HTTP do SDK |

Comandos de instalação (apenas referência de planejamento): `uv sync --group dev` para instalar; `uv add --group dev pytest pytest-cov pytest-socket` para registrar.

Observação: a escolha exata de bibliotecas de mock HTTP depende do SDK decidido (questão 1 do doc 00). O plano prioriza **não precisar delas**: o Adapter é testado unitariamente por um **cliente SDK falso injetado**, e a camada HTTP real só é exercitada na integração.

## 4. Estrutura de pastas **[PROPOSTA]**

```
supabase/
├── tests/
│   ├── conftest.py                  # fixtures globais, marcadores, regras de skip, guarda de ambiente
│   ├── fakes/                       # dublês reutilizáveis (não são testes)
│   │   ├── fake_table_gateway.py    # fake em memória do contrato de tabelas
│   │   ├── fake_storage_gateway.py  # fake em memória do contrato de arquivos
│   │   ├── fake_sdk_client.py       # imita o SDK, para testar o Adapter sem rede
│   │   ├── recording_logger.py      # logger que grava eventos para asserções
│   │   └── builders.py              # fábricas de dados de teste (registros, bytes de arquivos)
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_factory.py
│   │   ├── test_tables.py           # classe de tabelas com fake gateway
│   │   ├── test_storage.py          # classe de arquivos com fake gateway
│   │   ├── test_facade.py           # integradora: composição e delegação
│   │   ├── test_error_mapping.py    # exceções do SDK -> erros de domínio
│   │   ├── test_logging.py          # níveis, cores, campos, redação de segredos
│   │   └── test_adapters_offline.py # adapter real com fake_sdk_client
│   ├── contract/
│   │   ├── tables_contract.py       # bateria de comportamento (parametrizada)
│   │   ├── storage_contract.py
│   │   └── test_contracts.py        # roda a bateria em [fake, real]
│   ├── integration/
│   │   ├── test_tables_live.py
│   │   ├── test_storage_live.py
│   │   └── test_errors_live.py      # erros reais (não encontrado, sem permissão, duplicado)
│   ├── e2e/
│   │   └── test_facade_live.py      # fluxos completos via integradora
│   └── support/
│       ├── env_guard.py             # valida que o alvo é o projeto de TESTE
│       ├── cleanup.py               # registro e limpeza de recursos criados
│       └── test_schema.sql          # DDL do schema/tabelas de teste (aplicado manualmente ou via CLI)
└── pytest.ini                       # (ou seção em pyproject) rootdir, markers, testpaths
```

Regras de organização:

- Nomes de arquivo com prefixo `test_` só para o que o pytest deve coletar; `fakes/` e `support/` não são coletados.
- Nada em `supabase/tests/` importa código fora de `supabase/`. Isso preserva o desacoplamento exigido em 00 §3.3.
- Um **teste de arquitetura** simples (ver seção 11) verifica que nenhum módulo de `supabase/` importa o código antigo do projeto.

## 5. Testes unitários (sem Supabase real)

### 5.1 Princípio

Cada classe recebe suas dependências por DI. Nos unitários, as dependências são **fakes** dos contratos, nunca o SDK. A rede fica bloqueada por `pytest-socket` (`--disable-socket` aplicado ao escopo `unit`), de modo que um teste unitário que tente abrir conexão **falha com erro claro**.

### 5.2 Dublês **[PROPOSTA]**

| Dublê | Substitui | Comportamento |
|---|---|---|
| **FakeTableGateway** | Contrato de tabelas (Adapter) | Dicionários em memória por tabela; gera `id`; implementa filtros, ordenação, paginação, upsert; pode ser configurado para **falhar** (lançar erro do SDK simulado) em operações específicas |
| **FakeStorageGateway** | Contrato de arquivos (Adapter) | Dicionário `(bucket, caminho) -> (bytes, metadados)`; simula bucket inexistente, objeto inexistente, conflito de nome |
| **FakeSdkClient** | SDK do Supabase | Registra chamadas recebidas e devolve respostas/erros programados; usado só para testar o Adapter real em modo offline |
| **RecordingLogger** | Contrato de logger | Guarda cada evento (nível, mensagem, campos) em lista para asserções |
| **FixedClock / FakeTimer** | Relógio/medição de duração | Torna `duration_ms` determinístico |

Preferir **fakes com comportamento** a mocks de chamada (`Mock().assert_called_with`): fakes validam o resultado observável e sobrevivem a refatorações internas. Mocks puros ficam restritos a verificar **delegação** na integradora (ver 5.5).

### 5.3 Classe de tabelas

Cenários mínimos (todos com `FakeTableGateway` e `RecordingLogger`):

- Inserir um registro: retorna o registro com `id`; loga sucesso com tabela e duração.
- Inserir em lote: retorna todos; lote vazio é tratado conforme regra definida (erro de validação ou retorno vazio, ver questão 8).
- Buscar por id existente / inexistente (este último gera o erro de domínio "não encontrado" ou retorno vazio, conforme contrato).
- Buscar por filtros, com ordenação e paginação (limite, deslocamento, última página parcial).
- Atualizar: registro existente muda; inexistente gera erro de domínio.
- Deletar: remove; deletar inexistente segue a regra do contrato (idempotente ou erro, ver questão 8).
- Upsert (se aprovado): cria na primeira vez, atualiza na segunda.
- Validações de entrada: nome de tabela vazio, filtro inválido, payload vazio.
- Falha do gateway: o erro do SDK simulado é convertido em erro de domínio correto (detalhado na seção 9).

### 5.4 Classe de arquivos

- Upload: devolve metadados (bucket, caminho, tamanho, tipo); loga sem expor conteúdo.
- Upload com caminho já existente: erro de conflito **ou** sobrescrita, conforme a opção explícita do contrato.
- Download de objeto existente devolve exatamente os mesmos bytes; inexistente gera erro de domínio.
- URL de acesso: pública para bucket público, assinada com expiração para privado (comportamento simulado pelo fake).
- Exclusão: remove; exclusão de inexistente segue a regra do contrato.
- Listagem de pasta (se aprovada): ordem e prefixo corretos, pasta vazia retorna lista vazia.
- Validações: tipo/tamanho acima do limite (se questão 6 do doc 00 definir limites), caminho com `..` ou vazio, conteúdo de tamanho zero.
- Tipos variados: bytes de imagem, áudio, vídeo e documento (usar blobs sintéticos pequenos; o tipo vem da extensão/parâmetro, não do conteúdo).

### 5.5 Classe integradora (fachada)

Foco: **composição e delegação**, sem reimplementar lógica.

- Recebe as duas classes por injeção e expõe ponto único de entrada.
- Cada operação pública delega à classe correta (verificável com mocks simples ou fakes que registram chamadas).
- Não contém regra de tabela nem de storage: um teste garante que, com ambos os gateways fakes, a fachada **não** acessa nenhum deles diretamente.
- Falha em uma frente não afeta a outra (tabelas quebradas, arquivos continuam funcionando).
- Uso sem uma das frentes (se for permitido pela Factory) gera erro claro de configuração, não `AttributeError`.

### 5.6 Factory

- Constrói as três classes com dependências corretas a partir de uma configuração válida.
- Aceita **override** de qualquer dependência (logger, gateway, relógio): é o ponto de injeção usado em testes.
- Configuração inválida ou incompleta produz erro de configuração com **nomes** das variáveis faltantes, nunca valores.
- Cria instâncias independentes por chamada (sem estado global compartilhado), a menos que singleton seja decisão explícita.
- Não abre conexão de rede na construção (criação preguiçosa), o que permite testar a Factory com rede bloqueada. **[PROPOSTA]**

### 5.7 Config

- Lê variáveis do ambiente (injetado como dicionário nos testes, **sem tocar `os.environ` real**; usar `monkeypatch`).
- Aplica valores padrão (ex.: nível de log) e valida tipos (nível de log inválido gera erro claro).
- Falta de `URL` ou chave: erro que lista apenas os **nomes** ausentes.
- Garante que o objeto de config **mascara segredos** em `repr`/`str` (ex.: chave aparece como `***`).
- Distingue configuração de produção da de teste (ver seção 6.3).

### 5.8 Adapter em modo offline

Com o `FakeSdkClient`: verificar que cada método do contrato chama a operação correta do SDK com os parâmetros esperados (tabela, filtros, colunas, bucket, caminho, opções) e converte a resposta no formato do contrato. Aqui se testa a **tradução**, não o Supabase.

## 6. Testes de integração contra projeto de teste dedicado

### 6.1 Regra de ouro

> **Testes de integração nunca rodam contra produção, nem contra um projeto que contenha dados reais.** Rodam somente contra um projeto Supabase **criado exclusivamente para testes**, em um schema e buckets também exclusivos.

Medidas obrigatórias (defesa em profundidade):

1. **Projeto dedicado**: um projeto Supabase só para testes (ou, alternativa, a stack local, ver 6.6). Nunca reaproveitar o projeto de produção ou homologação.
2. **Variáveis próprias de teste**, separadas das de runtime (ver 6.3). Os testes **nunca** leem as variáveis de produção.
3. **Guarda de ambiente (`env_guard`)** executada no início da sessão: recusa rodar se o alvo não parecer de teste (ver 6.4).
4. **Prefixo/namespace de teste** em tudo que for criado (tabelas, buckets, caminhos), com nome único por execução (ver 6.5).
5. **Limpeza garantida** no teardown, mesmo em falha (ver 6.7).
6. **Credencial de menor privilégio possível** no projeto de teste e rotacionável sem impacto.

### 6.2 Isolamento de dados

| Recurso | Estratégia **[PROPOSTA]** |
|---|---|
| **Schema** | Schema dedicado (ex.: `it_tests`) ou tabelas com prefixo `it_` no `public` do projeto de teste. Preferência: schema dedicado (exige expô-lo na Data API do projeto de teste) |
| **Tabelas** | Tabelas fixas de teste, criadas **uma vez** por script SQL versionado (`support/test_schema.sql`), com colunas cobrindo tipos comuns (texto, número, booleano, JSON, timestamp). A integração **não faz DDL** (fora de escopo em 00 §5), então o schema de teste é preparado fora da suíte |
| **Linhas** | Cada teste insere linhas marcadas com um `run_id` (coluna `test_run_id`) único da sessão, e filtra/limpa apenas por esse `run_id` |
| **Buckets** | Bucket(s) de teste fixos e exclusivos (ex.: `it-tests-private`, `it-tests-public`), criados previamente na plataforma, um privado e um público, para cobrir os dois modos de URL |
| **Objetos** | Caminho sempre dentro de `<run_id>/<teste>/...`, nunca na raiz do bucket |
| **Paralelismo** | `run_id` por sessão evita colisão entre execuções simultâneas (dois devs ou CI + dev) |

### 6.3 Variáveis de ambiente de teste **[PROPOSTA]**

Nomes **próprios para testes**, separados dos de runtime e dos já existentes no `.env` (que pertencem à integração antiga). Os nomes finais dependem da decisão da questão 1 do doc 01 sobre nomenclatura.

| Variável (nome provisório) | Função |
|---|---|
| `SUPABASE_TEST_URL` | URL do projeto de teste |
| `SUPABASE_TEST_SECRET_KEY` | Chave de backend do projeto de teste |
| `SUPABASE_TEST_PUBLIC_KEY` | Chave pública (somente se algum cenário validar RLS/anon) |
| `SUPABASE_TEST_SCHEMA` | Schema/prefixo das tabelas de teste |
| `SUPABASE_TEST_TABLE` | Tabela principal de teste |
| `SUPABASE_TEST_BUCKET_PRIVATE` / `SUPABASE_TEST_BUCKET_PUBLIC` | Buckets de teste |
| `SUPABASE_TEST_PROJECT_REF` | Identificador esperado do projeto de teste (usado pela guarda) |

Onde ficam: arquivo **`.env.test`** na raiz (ou em `supabase/`), **fora do versionamento** (incluir no `.gitignore`), mais um **`.env.test.example`** versionado **só com os nomes** (sem valores), no mesmo espírito do doc 01 §4. Em CI, vêm de segredos do provedor de CI. Regras do doc 01 §5 valem integralmente: nunca colar valores em arquivos versionados, logs ou relatórios.

### 6.4 Guarda de ambiente (`env_guard`) **[PROPOSTA]**

Executada por fixture de sessão antes de qualquer teste de integração. Aborta a sessão (não apenas pula) se qualquer condição for verdadeira:

- `SUPABASE_TEST_PROJECT_REF` ausente ou diferente do identificador extraído de `SUPABASE_TEST_URL`.
- A URL de teste for **igual** à URL de runtime/produção conhecida (comparação feita por hash ou por igualdade sem exibir o valor).
- Nome de schema, tabela ou bucket **não começar** com o prefixo de teste (`it_`/`it-`).
- Variável `APP_ENV`/equivalente indicar produção (nome a definir).
- Um sinalizador explícito de consentimento, `SUPABASE_TEST_ALLOW_LIVE=1`, não estiver definido (**proteção contra execução acidental**: integração só roda de propósito).

A mensagem de abort cita **quais regras falharam**, nunca os valores.

### 6.5 Nomeação e unicidade **[PROPOSTA]**

- `run_id` = timestamp compacto + sufixo aleatório curto (ex.: `20261114T1530-a3f9`), gerado uma vez por sessão.
- Caminhos de arquivo: `<run_id>/<nome_do_teste>/<arquivo>`.
- Linhas: coluna `test_run_id = run_id`, e um campo de rótulo com o nome do teste.
- Nenhum teste depende de ordem de execução nem de dados deixados por outro.

### 6.6 Alternativas de ambiente de teste (decisão em aberto)

| Opção | Vantagem | Desvantagem |
|---|---|---|
| **Projeto Supabase de teste na nuvem** | Fidelidade total ao real (Storage, PostgREST, políticas) | Exige projeto extra, credenciais, rede; pode ter custo/limites do plano |
| **Stack local via Supabase CLI** (`supabase start`, Docker) | Sem custo, sem risco para dados reais, reproduzível; migrations e `config.toml` versionados, buckets definíveis por `config.toml` e `supabase db reset` volta ao estado conhecido | Exige Docker e CLI; recursos da plataforma podem diferir do hospedado (a própria documentação lista diferenças) |
| **Branch de banco do Supabase** | Isolamento por branch | Disponibilidade e custo dependem do plano |

Recomendação **[PROPOSTA]**: **stack local via CLI como padrão para desenvolvimento** (rápida, segura, sem credenciais reais) **e projeto de teste na nuvem para CI/verificação final**. A suíte é a mesma; muda apenas o conjunto de variáveis `SUPABASE_TEST_*`. Ver questão 1.

### 6.7 Limpeza e teardown **[PROPOSTA]**

- **Registro de recursos criados**: um `CleanupRegistry` (em `support/cleanup.py`) acumula tudo que o teste criou (linhas por id, objetos por caminho). Fixtures com `yield` removem **em ordem inversa** ao final do teste, mesmo se o teste falhar.
- **Varredura de segurança no fim da sessão**: remove linhas com `test_run_id = run_id` e objetos sob `<run_id>/`. Cobre vazamentos de testes que falharam no meio.
- **Varredura de órfãos antiga** (comando opcional): remove dados de execuções anteriores com `run_id` mais velho que N horas, filtrando **estritamente** pelo prefixo de teste. Nunca apaga sem o prefixo.
- A limpeza usa os mesmos contratos da integração (fachada), de modo que também valida deletar; mas, para não depender do código sob teste, a varredura final usa uma **rota independente** mínima (cliente SDK direto, restrito a `support/`). Alternativa mais simples: aceitar a dependência e registrar falha de limpeza como aviso visível.
- Falha de limpeza **não esconde** a falha do teste: ambas são reportadas.
- Nenhum teste apaga "tudo da tabela": sempre filtro por `run_id`.

### 6.8 O que a integração valida

- **Tabelas**: CRUD completo, lote, filtros (igual, comparação, `in`, texto), ordenação, paginação com mais de uma página, upsert, tipos (JSON, timestamp com fuso, nulo), unicidade violada, registro inexistente.
- **Arquivos**: upload e download com **igualdade byte a byte** (hash do conteúdo); tipos MIME variados (imagem, áudio, vídeo, documento); arquivo "grande" dentro do limite de teste; URL pública acessível e URL assinada acessível e **expirando**; listagem; exclusão e confirmação posterior de inexistência; caminho com caracteres especiais/acentos.
- **Erros reais**: bucket inexistente, objeto inexistente, tabela inexistente, coluna inválida, violação de unicidade, chave inválida (autenticação), URL inválida. Cada um deve resultar no **erro de domínio** esperado (seção 9).
- **Permissões** (se a decisão for usar chave pública além da secreta): com a chave pública, uma tabela com RLS restritiva nega acesso e vira erro de permissão do domínio.

## 7. Marcadores e skip condicional

### 7.1 Marcadores **[PROPOSTA]**

Registrados em `pytest.ini`/`pyproject` com `--strict-markers` (marcador desconhecido falha):

| Marcador | Significado |
|---|---|
| `unit` | Sem rede e sem credenciais (aplicado automaticamente a `tests/unit`) |
| `contract` | Bateria de contrato (fake sempre; real quando disponível) |
| `integration` | Requer rede **e** credenciais do projeto de teste |
| `e2e` | Fluxo completo via fachada, requer rede e credenciais |
| `storage` / `tables` | Filtros por frente |
| `slow` | Testes demorados (arquivo grande, expiração de URL) |
| `destructive` | Cria/apaga dados remotos (todo `integration` e `e2e` é, por definição) |

O `conftest.py` aplica marcadores **por localização** (pasta), para não depender de disciplina manual.

### 7.2 Regras de skip **[PROPOSTA]**

Comportamento por padrão (sem flags):

| Situação | Resultado |
|---|---|
| Rodar `pytest supabase/tests` sem `SUPABASE_TEST_*` | Unitários e contrato-com-fake rodam; `integration`/`e2e` são **puladas** com motivo explícito |
| Variáveis presentes, mas `SUPABASE_TEST_ALLOW_LIVE` ausente | Puladas com motivo "execução live não autorizada" |
| Variáveis presentes e autorizadas, mas guarda reprova | **Aborta a sessão** (erro, não skip), porque indica risco |
| Variáveis presentes, autorizadas e guarda ok | Rodam |

O motivo do skip lista **somente os nomes** das variáveis ausentes. Um `pytest_collection_modifyitems` no `conftest.py` aplica `skip` a itens `integration`/`e2e`; isso evita checar variável teste a teste.

Em CI **[PROPOSTA]**: um job "unit" sempre roda; um job "live" roda quando o segredo de teste existe e **falha** (em vez de pular) se `CI=true` e as variáveis estiverem ausentes, para que "pular em silêncio" não esconda ausência de cobertura. Flag/variável `SUPABASE_TEST_REQUIRE_LIVE=1` liga esse modo estrito.

## 8. Fixtures **[PROPOSTA]**

| Fixture | Escopo | Função |
|---|---|---|
| `recording_logger` | função | Logger que grava eventos para asserções |
| `fake_table_gateway` / `fake_storage_gateway` | função | Fakes zerados a cada teste |
| `tables_service` / `storage_service` / `facade` | função | Montados com fakes via Factory com overrides |
| `env_vars` | função | `monkeypatch` para ambiente controlado, sem tocar o `.env` real |
| `live_config` | sessão | Config de teste carregada de `SUPABASE_TEST_*`; roda a `env_guard` |
| `run_id` | sessão | Identificador único da execução |
| `live_facade` / `live_tables` / `live_storage` | sessão (cliente) / função (dados) | Serviços reais conectados ao projeto de teste |
| `cleanup` | função | `CleanupRegistry` com teardown automático em `yield` |
| `sample_record` / `sample_file_bytes` | função | Dados sintéticos (nunca dados reais) |
| `table_contract_target` / `storage_contract_target` | função, parametrizada | `[fake, real]`; a variante `real` leva o marcador `integration` |

Escopos: o **cliente** vivo é de sessão (evita reconectar), os **dados** são de função com limpeza, para manter independência entre testes.

Regra: fixtures nunca exibem nem retornam segredos em texto para o relatório; `repr` das configs é mascarado.

## 9. Teste do mapeamento de erros

O objetivo é garantir que **exceções do SDK nunca vazam** além do Adapter e que cada falha vira um **erro de domínio** estável (00 §3, proposta de erros próprios).

### 9.1 Tabela de mapeamento a validar **[PROPOSTA]**

Os nomes dos erros são provisórios; a taxonomia definitiva sai da etapa de arquitetura.

| Situação | Erro de domínio (provisório) |
|---|---|
| Registro não encontrado (busca única, update, delete conforme contrato) | `RecordNotFoundError` |
| Violação de unicidade / chave duplicada | `ConflictError` |
| Payload ou filtro inválido, coluna inexistente | `ValidationError` |
| Tabela inexistente | `TableNotFoundError` |
| Bucket ou objeto inexistente | `BucketNotFoundError` / `FileNotFoundInStorageError` |
| Conflito de nome no upload (sem sobrescrita) | `ConflictError` |
| Chave inválida ou sem permissão (RLS, política de storage) | `PermissionDeniedError` / `AuthenticationError` |
| Timeout, DNS, rede indisponível | `ConnectionError` do domínio (com indicação de "reexecutável") |
| Limite de taxa / servidor indisponível | `ServiceUnavailableError` |
| Config ausente/inválida | `ConfigurationError` |
| Erro não classificado | `SupabaseIntegrationError` (base), preservando a causa |

### 9.2 Como testar

- **Unitário (Adapter offline)**: o `FakeSdkClient` é programado para lançar cada tipo de falha (resposta com status/código equivalentes, exceções de rede, JSON inesperado). Teste **parametrizado** (uma linha por situação) afirma o tipo exato do erro de domínio.
- **Hierarquia**: todos herdam de uma base comum; um teste confirma `isinstance` e que capturar a base captura todos.
- **Causa preservada**: o erro de domínio mantém a exceção original em `__cause__` (para depuração), mas a **mensagem** é sanitizada.
- **Sem vazamento**: um teste varre as mensagens e `repr` dos erros e confirma que não contêm chave, URL completa com credenciais nem conteúdo de registros/arquivos.
- **Atributos úteis**: erros carregam contexto estruturado (operação, tabela/bucket, identificador), não só texto.
- **Fachada**: confirma que erros de domínio propagam **sem serem reembrulhados** (mesmo tipo e contexto).
- **Integração**: cada situação reproduzível no projeto de teste (6.8) confirma o mesmo tipo de erro que o fake produz. Isso valida a tabela de mapeamento contra o comportamento real do Supabase, que é onde esse mapeamento costuma quebrar.
- **Códigos inesperados**: um teste garante que status ou códigos desconhecidos caem no erro base, nunca em `KeyError`/`AttributeError`.

## 10. Teste dos logs

Cobre os requisitos de 00 §3.2: nível configurável, verboso porém legível, colorido, sem segredos, logger injetado.

### 10.1 Pontos a validar

| Aspecto | Como testar |
|---|---|
| **Nível configurável** | Parametrizar `DEBUG/INFO/WARNING/ERROR`; emitir um evento de cada nível; afirmar que só os eventos `>=` o nível configurado aparecem. Nível inválido gera `ConfigurationError` |
| **Campos estruturados** | Eventos de operação contêm: operação, alvo (tabela ou bucket), identificador(es), duração em ms, resultado (sucesso/falha). Usar `RecordingLogger` para checar campos por nome, sem depender da formatação textual |
| **Detalhe por nível** | `DEBUG` traz parâmetros (sanitizados); `INFO` traz resumo; `ERROR` traz tipo do erro de domínio e contexto |
| **Cores** | Capturar a saída (`capsys`/stream em memória) e checar **sequências ANSI** esperadas por nível (cores distintas para debug, info, aviso, erro). Com `NO_COLOR` definido ou saída não-TTY, **não** emitir ANSI (comportamento a confirmar, questão 5) |
| **Sem segredos** | Teste de "canário": configurar uma chave sintética reconhecível (ex.: `TEST-SECRET-CANARY-123`) e um registro/arquivo com conteúdo sintético sensível; executar todas as operações em nível `DEBUG` com falhas e sucessos; afirmar que o canário **não aparece** em nenhuma saída de log, mensagem de erro ou `repr` |
| **Redação de campos** | Valores de campos marcados como sensíveis (chaves, tokens, cabeçalhos de autorização) aparecem mascarados |
| **Conteúdo de arquivos e registros** | Em nenhum nível o corpo do arquivo ou o payload completo é logado; no máximo, tamanho, tipo, contagem de campos/linhas |
| **Injeção** | As classes aceitam qualquer objeto que cumpra o contrato de logger (fake grava eventos); nenhuma instancia logger global por conta própria |
| **Sem logger** | Se nenhum logger é fornecido, a Factory usa um padrão; se o logger for "nulo" (null object), as classes funcionam sem erro |
| **Eventos de erro** | Um erro de domínio gera **um** log de erro (sem duplicar em cada camada); verificar contagem de eventos por falha |
| **Correlação** | Se houver identificador de operação, ele é igual entre eventos de início/fim da mesma operação **[PROPOSTA]** |
| **Falha do logger** | Erro dentro do logger não derruba a operação de negócio (isolamento) **[PROPOSTA]** |

Evitar testes frágeis de texto exato: asserções sobre **campos e níveis** do `RecordingLogger`; apenas um pequeno conjunto de testes de formatação checa ANSI e layout.

## 11. Testes de arquitetura e de contrato adicionais

- **Independência**: teste que varre os imports de `supabase/` e falha se algum módulo importar o código da integração antiga ou de outras partes do projeto (`src/`, `web_services.py`, etc.). Detecção por inspeção estática dos `import` (AST), sem executar.
- **Desacoplamento do SDK**: afirma que apenas o pacote `adapters/` importa o SDK do Supabase; `contracts/`, classes de tabela/arquivo, fachada e factory não o importam.
- **Liskov via contrato**: a bateria de contrato roda em fake e real e tem de passar nos dois (seção 2).
- **Substituibilidade**: a fachada funciona igual com qualquer combinação de fakes.
- **Sem estado global**: duas fachadas criadas na mesma sessão não compartilham estado.

## 12. Cobertura mínima desejada **[PROPOSTA]**

| Escopo | Meta de cobertura de linhas (só unit + contrato-com-fake) | Observações |
|---|---|---|
| Classe de tabelas | >= 95% | Inclui ramos de erro e validação |
| Classe de arquivos | >= 95% | Idem |
| Classe integradora | 100% | É pequena (compõe e delega) |
| Factory | >= 95% | Inclui overrides e erros de configuração |
| Config | >= 95% | Inclui mascaramento |
| Mapeador de erros | 100% dos ramos | Tabela parametrizada |
| Logger | >= 90% | Cores e níveis |
| Adapters | >= 85% no modo offline; o restante coberto pela integração | O que depende de rede real fica em `integration` |
| **Total do pacote `supabase/`** | **>= 90% de linhas e >= 80% de ramos** | Medido com `pytest-cov`, excluindo `tests/` |

Regras:

- A meta é aplicada em **CI como falha** (`--cov-fail-under`), calculada **sem** os testes de integração (para ser reproduzível sem credenciais). A cobertura de integração é informativa.
- Cobertura é piso de qualidade, não objetivo: **cenários de borda e de erro** pesam mais que o percentual.

## 13. Como rodar **[PROPOSTA]**

Comandos de referência (a partir da raiz do repositório; ajustar caminhos após fechar a estrutura):

```bash
# instalar dependências, incluindo o grupo dev
uv sync --group dev

# apenas unitários e contrato com fake (padrão; sem rede, sem credenciais)
uv run pytest supabase/tests -m "not integration and not e2e"

# tudo que for possível; integração/e2e são puladas se faltarem variáveis
uv run pytest supabase/tests

# somente integração live (exige SUPABASE_TEST_* e SUPABASE_TEST_ALLOW_LIVE=1)
uv run pytest supabase/tests -m integration

# somente a frente de arquivos / de tabelas
uv run pytest supabase/tests -m storage
uv run pytest supabase/tests -m tables

# fluxos completos pela fachada
uv run pytest supabase/tests -m e2e

# cobertura (piso aplicado apenas aos testes offline)
uv run pytest supabase/tests -m "not integration and not e2e" \
  --cov=supabase --cov-report=term-missing --cov-fail-under=90

# modo estrito de CI: ausência de credenciais vira falha, não skip
SUPABASE_TEST_REQUIRE_LIVE=1 uv run pytest supabase/tests -m "integration or e2e"

# exibir logs em tempo real ao depurar um teste
uv run pytest supabase/tests/unit/test_logging.py -s -o log_cli=true -o log_cli_level=DEBUG
```

Atenção ao **nome da pasta**: um diretório chamado `supabase/` na raiz pode **colidir com o pacote Python `supabase`** (o SDK oficial `supabase-py`) ao importar. Ver questão 4; é um risco concreto que afeta como os testes importam o código e deve ser resolvido na etapa de arquitetura (por exemplo, com um nome de pacote interno distinto do da pasta).

## 14. Critérios de aceite por classe

Um item só é considerado pronto quando **todos** os critérios dele passam e a cobertura mínima da seção 12 é atingida.

### 14.1 Classe de tabelas

- [ ] Todos os cenários da seção 5.3 passam com `FakeTableGateway`.
- [ ] Bateria de contrato de tabelas passa em **fake e real**.
- [ ] Integração (6.8) cobre CRUD, lote, filtros, paginação, upsert (se aprovado) e erros reais, com dados isolados por `run_id` e limpos.
- [ ] Cada falha vira o erro de domínio correto (tabela 9.1), sem exceção do SDK vazando.
- [ ] Nenhum payload completo ou segredo aparece em logs (teste canário).
- [ ] Cobertura >= 95%.

### 14.2 Classe de arquivos

- [ ] Todos os cenários da seção 5.4 passam com `FakeStorageGateway`.
- [ ] Bateria de contrato de arquivos passa em **fake e real**.
- [ ] Integração: upload/download com igualdade byte a byte (hash), tipos variados, URL pública e assinada (com expiração), listagem (se aprovada), exclusão e verificação de inexistência.
- [ ] Erros (bucket/objeto inexistente, conflito, permissão) mapeados corretamente.
- [ ] Logs registram tamanho/tipo/caminho, nunca o conteúdo.
- [ ] Cobertura >= 95%.

### 14.3 Classe integradora (fachada)

- [ ] Recebe dependências por DI e depende só de contratos.
- [ ] Cada operação delega à classe correta; nenhuma lógica própria de tabela/storage.
- [ ] Falha de uma frente não afeta a outra.
- [ ] Erros de domínio propagam sem reembrulhar.
- [ ] E2E: ao menos um fluxo completo (ex.: criar registro, anexar arquivo, recuperar ambos, remover ambos) verde no projeto de teste, com limpeza confirmada.
- [ ] Cobertura 100%.

### 14.4 Factory

- [ ] Constrói as três classes, com overrides de qualquer dependência.
- [ ] Configuração inválida gera `ConfigurationError` listando apenas nomes de variáveis.
- [ ] Sem estado global compartilhado; sem rede na construção.
- [ ] Usada pelos testes de integração e pela suíte unitária (mesma montagem, dependências diferentes), provando que a DI funciona.
- [ ] Cobertura >= 95%.

### 14.5 Config

- [ ] Carrega de dicionário/ambiente injetado, aplica padrões e valida tipos.
- [ ] Mascara segredos em `repr`/`str` e em mensagens de erro.
- [ ] Separa explicitamente a config de teste da de produção; a guarda de ambiente (6.4) reprova alvo suspeito.
- [ ] Nível de log inválido e variáveis ausentes geram erro claro.
- [ ] Cobertura >= 95%.

### 14.6 Transversais (logs, erros, independência)

- [ ] Testes de nível, cores, campos e canário de segredos (seção 10) verdes.
- [ ] Teste de arquitetura confirma ausência de imports da integração antiga e do restante do projeto (seção 11).
- [ ] Suíte unitária roda **sem rede** (`pytest-socket`) e sem nenhum `.env` presente.
- [ ] Suíte sem credenciais termina verde, com integração **pulada** e motivo explícito; em CI estrito, falha se faltar credencial.
- [ ] Nenhum dado de teste remanescente no projeto de teste ao final de uma execução bem-sucedida (varredura final retorna zero).

## 15. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Rodar integração contra produção por engano | Projeto dedicado, variáveis `SUPABASE_TEST_*` separadas, `env_guard`, consentimento explícito (`ALLOW_LIVE`), prefixos obrigatórios |
| Fake divergir do comportamento real | Bateria de contrato rodando em ambos |
| Dados órfãos no projeto de teste | Teardown em `yield`, varredura por `run_id`, varredura de órfãos por prefixo e idade |
| Vazamento de segredo em logs/relatórios | Teste canário, mascaramento em config, `repr` seguro, revisão de `--tb` e saída do CI |
| Testes lentos ou instáveis por rede | Poucos testes live, escopo de sessão para o cliente, `slow` isolado, tentativas apenas em operações idempotentes de leitura **[PROPOSTA]** |
| Colisão entre execuções paralelas | `run_id` único e caminhos/linhas por `run_id` |
| Colisão de nome `supabase` com o SDK | Resolver na arquitetura (questão 4) |
| Limites/custos do plano no projeto de teste | Preferir stack local no dia a dia; live só para CI/verificação |

## 16. Questões em aberto

| # | Questão | Recomendação |
|---|---|---|
| 1 | Qual ambiente de integração usar: projeto de teste na nuvem, stack local via Supabase CLI (Docker) ou ambos? | **Ambos**: local para desenvolvimento diário, nuvem para CI/verificação final. Mesma suíte, variáveis diferentes |
| 2 | Adotar `pytest` como framework da suíte (mesmo o repo não tendo suíte pytest)? Aceita um grupo `dev` em `pyproject.toml`? | **Sim**, isolado em `supabase/tests/`, sem exigir adoção no resto do projeto |
| 3 | Onde declarar dependências de teste: grupo `dev` no `pyproject.toml` da raiz ou um `pyproject` próprio em `supabase/`? | Grupo `dev` na raiz (uv é a fonte de verdade); revisitar se `supabase/` virar pacote independente |
| 4 | O nome da pasta/pacote `supabase` colide com o pacote do SDK `supabase` ao importar. Como nomear o pacote Python interno? | Manter a pasta `supabase/` como contêiner de docs e testes, e dar ao pacote de código um nome interno distinto (ex.: `bai_supabase`); decidir na etapa de arquitetura |
| 5 | Comportamento das cores em não-TTY/CI e com `NO_COLOR`: desativar automaticamente? | Desativar automaticamente fora de TTY ou com `NO_COLOR`, com opção de forçar por configuração |
| 6 | Quais nomes de variáveis de teste (`SUPABASE_TEST_*`) e onde fica o `.env.test`? | Nomes próprios com prefixo `SUPABASE_TEST_`; `.env.test` na raiz, ignorado pelo Git, mais `.env.test.example` só com nomes |
| 7 | Quem cria o projeto/buckets/tabelas de teste e aplica `test_schema.sql` (a integração não faz DDL)? | Preparação manual única (ou via Supabase CLI/migrations) fora da suíte; o guia 01 se aplica (somente leitura por agentes, sem criar nada sem pedido explícito) |
| 8 | Semântica de deletar/atualizar inexistente e de lote vazio: erro ou idempotente? | Atualizar inexistente: erro `RecordNotFoundError`. Deletar inexistente: idempotente (sem erro) com log de aviso. Lote vazio: erro de validação. Fixar no contrato e refletir na bateria |
| 9 | Meta de cobertura de 90% linhas / 80% ramos é adequada? | Sim como piso inicial, revisitar após a primeira implementação |
| 10 | CI: haverá pipeline (que provedor) para rodar o job "live" com segredo de teste? | Definir junto da fase de plano de implementação; até lá, rodar manualmente |
| 11 | A suíte deve incluir cenários de RLS (chave pública), dependendo da decisão de credenciais (questão 2 do doc 01)? | Só se a chave pública for usada pela integração; caso contrário, fora de escopo |
| 12 | Os testes devem usar `pytest-asyncio` (depende da decisão sync/async do doc 00)? | Decidir junto da questão 2 do doc 00; o plano é neutro e prevê parametrizar o adaptador nos dois modos se ambos existirem |

## 17. Referências

URLs consultadas ou usadas como fundamento:

- Supabase, desenvolvimento local e migrations (CLI, `supabase start`, `supabase db reset`, `seed.sql`, buckets por `config.toml` e limitações do ambiente local): <https://supabase.com/docs/guides/local-development/database-migrations>
- Supabase, visão geral do desenvolvimento local (ponto de entrada indicado): <https://supabase.com/docs/guides/local-development/overview>
- Supabase, quickstart com Flask (referência já adotada nos docs 00 e 01): <https://supabase.com/docs/guides/getting-started/quickstarts/flask>
- Documentos internos: [spec.md](../spec.md), [01-variaveis-de-ambiente.md](01-variaveis-de-ambiente.md)

Observação: recomendações sobre `pytest` (fixtures, marcadores, `skipif`, `caplog`, `capsys`, `monkeypatch`) e sobre `pytest-cov`/`pytest-socket` baseiam-se em prática consolidada da comunidade; confirmar versões e opções atuais na documentação dessas ferramentas antes de implementar.
