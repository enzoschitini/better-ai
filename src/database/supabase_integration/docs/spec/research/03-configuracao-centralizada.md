# Configuração centralizada da integração Supabase

> **Material de pesquisa (refinamento técnico).** A visão geral citada aqui como "00" / "visão geral" agora vive em [../spec.md](../spec.md). As "Questões em aberto" deste arquivo estão **consolidadas e resolvidas em [../decisions.md](../decisions.md)**, que prevalece em caso de divergência. Tarefas de implementação: [../tasks.md](../tasks.md).

> **Status: rascunho de planejamento.** Nenhum código foi escrito. Itens marcados como **[PROPOSTA]** são sugestões a validar; decisões que dependem do usuário estão em "Questões em aberto" (seção 11), cada uma com recomendação.
> Documentos relacionados: [spec.md](../spec.md) (princípios, três classes, logs, desacoplamento) e [01-variaveis-de-ambiente.md](01-variaveis-de-ambiente.md) (como obter e onde guardar as variáveis).

## 1. Contexto e objetivo

A integração tem três classes (tabelas, arquivos, integradora/fachada), uma Factory e um logger injetado. Todas precisam de parâmetros (URL, chave, buckets, schema, timeouts, limites). Sem um ponto único para isso, cada classe acabaria lendo `os.environ` por conta própria, o que gera:

- validação espalhada e erros tardios (a falha aparece só na primeira chamada ao banco);
- testes dependentes do ambiente da máquina;
- risco de vazar segredos em logs e mensagens de erro.

**Objetivo:** um único objeto de configuração, **imutável**, **carregado e validado na inicialização**, que **falha cedo** com mensagem clara (nomes das variáveis faltantes ou inválidas, nunca valores) e é **injetado** por construtor, sem variáveis globais.

## 2. Decisões e recomendações (resumo)

| # | Decisão | Recomendação |
|---|---|---|
| 1 | Forma da configuração | Um objeto de valor imutável (nome provisório `SupabaseSettings`), com campos tipados. **[PROPOSTA]** |
| 2 | Origem dos valores | Duas camadas: um **leitor de fonte** (lê `os.environ`/`.env`) e um **construtor/validador** que produz o objeto. O objeto em si não lê o ambiente. **[PROPOSTA]** |
| 3 | Falha | Na inicialização, uma única exceção de domínio agregando **todos** os problemas (não só o primeiro). |
| 4 | Nomes de variáveis | Ver seção 6 e Questão 1: recomendação é **nomes próprios com prefixo `SBX_`**, com fallback opcional aos `SUPABASE_*` legados desligado por padrão. **[PROPOSTA]** |
| 5 | Ambientes | Variável seletora `SBX_ENV` (`dev`/`homol`/`prod`) que define **padrões** de segurança e log; os valores de credenciais vêm sempre do ambiente do processo (um conjunto por ambiente). **[PROPOSTA]** |
| 6 | Injeção | Só a Factory conhece a origem da configuração; as três classes e o logger recebem o objeto (ou a fatia que usam) pelo construtor. |
| 7 | Modelo de variáveis | Arquivo só com nomes, versionado, mantido junto desta pasta, com checagem de consistência contra a lista de parâmetros deste documento. |

## 3. O objeto de configuração

### 3.1 Propriedades exigidas

- **Imutável:** após criado, nenhum campo muda (objeto congelado). Mudar configuração = criar outro objeto.
- **Tipado:** inteiros, booleanos, durações e listas já convertidos; ninguém consome strings cruas.
- **Validado na criação:** obrigatoriedade, formato (URL com esquema `https`, inteiros positivos, enum de nível de log) e coerência entre campos (ex.: `retry_backoff_max >= retry_backoff_base`).
- **Sem segredo no `repr`/`str`/log:** campos sensíveis são mascarados (`***`). Há um método de "resumo seguro" para log que lista nomes e se o valor está definido, nunca o valor.
- **Sem acesso a ambiente ou rede ao ser usado:** só dados.
- **Dividido em fatias** (seção 3.2) para respeitar ISP: cada classe recebe só o que precisa.

### 3.2 Estrutura em fatias **[PROPOSTA]**

| Fatia | Quem consome | Conteúdo |
|---|---|---|
| Conexão | Factory/Adapter | URL, chave, schema, timeout de rede, retries |
| Tabelas | Classe de tabelas | schema padrão, limites de paginação, timeout de consulta |
| Arquivos | Classe de arquivos | buckets, limites e tipos permitidos, expiração de URL assinada, timeout de upload |
| Log | Logger | nível, cores, formato, mascaramento |
| Ambiente | Factory | `env`, flags de segurança do ambiente |

O objeto raiz compõe as fatias. Cada classe depende apenas da sua fatia, não do objeto inteiro.

### 3.3 Pseudo-assinaturas (contrato, sem implementação)

```
SupabaseSettings            # imutável; compõe: connection, tables, storage, logging, environment
  .safe_summary() -> dict   # nomes + "definido/não definido"; nunca valores de segredo
  (repr/str mascaram segredos)

SettingsSource (contrato)   # origem dos pares nome->texto
  .get(name) -> str | None
  implementações: EnvironmentSource, DotenvFileSource, DictSource (testes)

SettingsLoader
  .load(source: SettingsSource) -> SupabaseSettings   # valida tudo; levanta SettingsError

SettingsError               # exceção de domínio
  .missing: lista de nomes de variáveis obrigatórias ausentes
  .invalid: lista de (nome, motivo)  # motivo sem o valor
```

## 4. Falha cedo e mensagens

### 4.1 Regras

1. A validação roda **uma vez**, em `SettingsLoader.load`, antes de qualquer cliente ser criado. O processo não chega a abrir conexão com configuração inválida.
2. **Agregar erros:** reportar todos os problemas de uma vez.
3. **Nunca incluir valores** na mensagem, nem parciais (nada de "começa com `eyJ...`"). Para formatos inválidos, dizer a regra violada, não o conteúdo.
4. A mensagem diz **o que fazer** e aponta para o doc 01 e para o arquivo modelo.
5. Valores vazios (`""`) contam como ausentes.
6. Variáveis desconhecidas com o prefixo da integração (provável erro de digitação) geram **aviso** (não erro), listando só o nome.

### 4.2 Exemplo de mensagem (cenário: ambiente `prod` incompleto)

```
SettingsError: configuração do Supabase inválida (ambiente: prod)
  Ausentes (obrigatórias):
    - SBX_URL
    - SBX_SECRET_KEY
  Inválidas:
    - SBX_HTTP_TIMEOUT_SECONDS: deve ser número > 0
    - SBX_LOG_LEVEL: deve ser um de DEBUG, INFO, WARNING, ERROR
  Ver: supabase/spec/research/01-variaveis-de-ambiente.md e supabase/.env.example
```

Nenhum valor aparece.

## 5. Parâmetros

Convenção de nomes na tabela: prefixo `SBX_` é a recomendação **[PROPOSTA]** da seção 6; se a Questão 1 for decidida de outro modo, só o prefixo muda. "Seg." = segredo (nunca logar). Tipos: `str`, `int`, `float`, `bool`, `enum`, `lista` (separada por vírgula).

### 5.1 Ambiente e conexão

| Variável | Obrig. | Padrão | Tipo | Seg. | Descrição |
|---|---|---|---|---|---|
| `SBX_ENV` | não | `dev` | enum (`dev`,`homol`,`prod`) | não | Ambiente lógico; muda os padrões de log e a rigidez da validação (seção 7). |
| `SBX_URL` | **sim** | n/d | str (URL `https`) | não | Project URL do projeto Supabase. |
| `SBX_SECRET_KEY` | **sim** (backend) | n/d | str | **sim** | Chave de servidor (`service_role`/*secret*). Uso exclusivo do backend (doc 01, seção 5). |
| `SBX_PUBLISHABLE_KEY` | não | vazio | str | sim (tratar como) | Chave pública (`anon`/*publishable*). Só se a integração usar acesso sujeito a RLS (Questão 3). |
| `SBX_DB_SCHEMA` | não | `public` | str | não | Schema usado pela API de dados. O schema precisa estar exposto na Data API do projeto. |
| `SBX_DB_CONNECTION_STRING` | não | vazio | str | **sim** | Só se houver acesso direto Postgres (doc 01, Questão 4). Fora do caminho padrão. |
| `SBX_HTTP_TIMEOUT_SECONDS` | não | `10` | float > 0 | não | Timeout de requisições à API de dados. |
| `SBX_MAX_RETRIES` | não | `3` | int ≥ 0 | não | Tentativas extras em falhas transitórias (rede, 5xx, 429). `0` desliga. |
| `SBX_RETRY_BACKOFF_BASE_SECONDS` | não | `0.5` | float > 0 | não | Espera inicial do backoff exponencial. |
| `SBX_RETRY_BACKOFF_MAX_SECONDS` | não | `8` | float ≥ base | não | Teto da espera entre tentativas. |

### 5.2 Tabelas

| Variável | Obrig. | Padrão | Tipo | Descrição |
|---|---|---|---|---|
| `SBX_TABLES_ALLOWLIST` | não | vazio (= qualquer tabela) | lista | Se preenchida, a classe de tabelas só opera nessas tabelas. **[PROPOSTA]** útil em prod. |
| `SBX_TABLES_DEFAULT_PAGE_SIZE` | não | `50` | int 1..`MAX` | Tamanho padrão de página em listagens. |
| `SBX_TABLES_MAX_PAGE_SIZE` | não | `1000` | int ≥ 1 | Teto de página (a API de dados tem limite próprio de linhas por requisição, configurável no projeto; o teto aqui deve ser ≤ esse limite). |
| `SBX_TABLES_BATCH_SIZE` | não | `500` | int ≥ 1 | Tamanho máximo de lote em inserção/upsert em lote; lotes maiores são fatiados. |

### 5.3 Arquivos (storage)

| Variável | Obrig. | Padrão | Tipo | Descrição |
|---|---|---|---|---|
| `SBX_BUCKET_DEFAULT` | **sim** se usar storage | n/d | str | Bucket usado quando a chamada não indica outro. |
| `SBX_BUCKETS_ALLOWLIST` | não | só o padrão | lista | Buckets que a classe de arquivos aceita. Evita escrever em bucket por engano. |
| `SBX_BUCKETS_PUBLIC` | não | vazio | lista | Subconjunto de buckets públicos (define se a recuperação devolve URL pública ou assinada). A visibilidade real é do bucket na plataforma; esta lista só informa a integração, e a Factory pode conferir no startup (opcional). |
| `SBX_STORAGE_MAX_FILE_BYTES` | não | `52428800` (50 MiB) | int > 0 | Tamanho máximo por arquivo, validado **antes** do upload. Ajustar também ao limite global de upload do projeto e ao limite por bucket. |
| `SBX_STORAGE_ALLOWED_MIME` | não | vazio (= qualquer tipo) | lista | Tipos MIME aceitos (aceitar curinga como `image/*`). |
| `SBX_STORAGE_SIGNED_URL_TTL_SECONDS` | não | `3600` | int > 0 | Validade padrão de URL assinada. |
| `SBX_STORAGE_UPLOAD_TIMEOUT_SECONDS` | não | `120` | float > 0 | Timeout de upload/download (maior que o da API de dados). |
| `SBX_STORAGE_UPSERT_DEFAULT` | não | `false` | bool | Se um upload sobrescreve arquivo existente por padrão. |
| `SBX_STORAGE_CACHE_CONTROL_SECONDS` | não | `3600` | int ≥ 0 | Cache-control aplicado no upload. |

### 5.4 Log

| Variável | Obrig. | Padrão | Tipo | Descrição |
|---|---|---|---|---|
| `SBX_LOG_LEVEL` | não | por ambiente (seção 7) | enum (`DEBUG`,`INFO`,`WARNING`,`ERROR`) | Nível mínimo. |
| `SBX_LOG_COLOR` | não | `auto` | enum (`auto`,`on`,`off`) | `auto` = colore só se o terminal for interativo e `NO_COLOR` não estiver definida. |
| `SBX_LOG_FORMAT` | não | `pretty` | enum (`pretty`,`json`) | `pretty` para terminal; `json` para ingestão em produção. **[PROPOSTA]** |
| `SBX_LOG_SLOW_MS` | não | `1000` | int ≥ 0 | Operações acima desse tempo são destacadas (aviso). **[PROPOSTA]** |
| `SBX_LOG_MAX_FIELD_CHARS` | não | `200` | int ≥ 20 | Trunca valores longos em campos de log (evita despejar registro/arquivo inteiro). |

### 5.5 Itens deliberadamente fora da lista

- **Senha do banco e string de conexão** só entram se a Questão 4 do doc 01 resultar em acesso direto; por padrão a integração usa apenas a API (URL + chave).
- **Nenhuma variável liga a "lógica de negócio"**; só infraestrutura.

## 6. Estratégia de nomes de variáveis

O `.env` do projeto **já contém** variáveis `SUPABASE_*` usadas pela integração antiga. Conferindo apenas os nomes (valores não lidos): `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `SUPABASE_PROJECT_HOST`, `SUPABASE_PROJECT_NAME`, `SUPABASE_DATABASE_URL`, `SUPABASE_DATABASE_PASSWORD`.

| Aspecto | A. Reutilizar `SUPABASE_*` | B. Nomes próprios isolados (ex.: `SBX_*`) |
|---|---|---|
| Esforço de setup | Mínimo; já existem no `.env` e nos ambientes | Preencher um conjunto novo por ambiente |
| Isolamento | **Quebra** a regra de independência (00, seção 3.3): as duas integrações dependem do mesmo contrato implícito | Total; nenhuma colisão |
| Risco de regressão | Alterar valor/semântica para a nova integração afeta a antiga (e vice-versa) | Nenhum cruzamento |
| Semântica | Nomes legados podem ter significado ambíguo (`SUPABASE_URL` vs. `SUPABASE_DATABASE_URL`) | Semântica definida neste doc |
| Convivência durante a transição | Difícil: mudar a chave de uma muda a outra | Fácil: coexistem |
| Remoção da antiga depois | Renomear/limpar variáveis, risco de esquecer | Basta apagar as antigas |
| Convenção do ecossistema | Familiar (`SUPABASE_URL` é nome comum em exemplos oficiais) | Menos familiar; documentar |
| Duplicação de segredos | Nenhuma | A mesma chave aparece sob dois nomes (até a antiga ser removida) |

**Recomendação [PROPOSTA]: opção B**, com prefixo próprio curto e único (`SBX_`, ajustável), porque preserva o requisito central de independência e permite coexistência e remoção limpa da integração antiga. A duplicação de valor é custo aceito e temporário.

**Mitigação opcional:** um `SettingsSource` decorador de **fallback** que, se uma variável `SBX_*` obrigatória estiver ausente, tenta o nome legado equivalente (mapa fixo `SBX_URL`→`SUPABASE_URL`, `SBX_SECRET_KEY`→`SUPABASE_SECRET_KEY`). Fica **desligado por padrão** (`SBX_ALLOW_LEGACY_FALLBACK=false`), é explícito no log (só o nome usado, nunca o valor) e serve só para acelerar testes locais. Se o usuário preferir a opção A, o mapa vira a lista oficial de nomes e este fallback deixa de existir.

Regras de nomenclatura (valem em qualquer opção): prefixo único; `SCREAMING_SNAKE_CASE`; sufixo com unidade (`_SECONDS`, `_BYTES`, `_MS`); listas separadas por vírgula, sem espaços significativos; booleanos aceitos: `true/false/1/0/yes/no` (sem diferenciar maiúsculas).

## 7. Múltiplos ambientes (dev / homologação / produção)

O projeto tem três ambientes (CLAUDE.md: prod, homol, dev, cada um com seu deploy). Modelo **[PROPOSTA]**:

- **Um conjunto de variáveis por ambiente**, fornecido pelo ambiente do processo (variáveis da plataforma de deploy; `.env` local só em dev). Não há um arquivo único com os três conjuntos.
- `SBX_ENV` seleciona **padrões** e **regras de rigidez**, não credenciais:

| Aspecto | `dev` | `homol` | `prod` |
|---|---|---|---|
| `SBX_LOG_LEVEL` padrão | `DEBUG` | `INFO` | `WARNING` |
| `SBX_LOG_COLOR` padrão | `auto` | `auto` | `off` |
| `SBX_LOG_FORMAT` padrão | `pretty` | `pretty` | `json` |
| `SBX_TABLES_ALLOWLIST` | opcional | recomendada | **obrigatória** |
| `SBX_BUCKETS_ALLOWLIST` | opcional | recomendada | **obrigatória** |
| Fallback legado | permitido se ligado | proibido | proibido |
| Carregar `.env` de arquivo | permitido | não | não |

- **Proteção contra misturar ambientes:** variável opcional `SBX_EXPECTED_PROJECT_REF` (identificador do projeto, não segredo) validada contra a URL; se não bater com o esperado para o `SBX_ENV`, falha na inicialização. Evita apontar prod com credenciais de dev. **[PROPOSTA]**
- **Precedência (maior vence):** valor passado explicitamente na criação (testes) > variável de ambiente do processo > arquivo `.env` (só dev) > padrão do ambiente > padrão global.
- Projetos Supabase distintos por ambiente ainda é decisão do usuário (Questão 3 do doc 01 / Questão 5 deste).

## 8. Injeção de dependência (sem variáveis globais)

### 8.1 Quem lê o quê

```
Ponto de entrada (composição) ──▶ SettingsLoader(source) ──▶ SupabaseSettings (imutável)
                                                                  │
                                                       Factory.create(settings)
                                    ┌─────────────────────┬───────┴──────────┬──────────────┐
                                    ▼                     ▼                  ▼              ▼
                            Logger(settings.logging)  Adapter(settings.connection)   ...
                                                          │
                              Classe de tabelas(adapter, settings.tables, logger)
                              Classe de arquivos(adapter, settings.storage, logger)
                              Integradora(tabelas, arquivos, logger)
```

### 8.2 Regras

1. **Só o ponto de composição** (script, testes ou, no futuro, o ponto de integração com o projeto) escolhe a `SettingsSource` e chama o `SettingsLoader`. Nenhuma classe da integração importa `os`/`dotenv`.
2. A **Factory** recebe `SupabaseSettings` e devolve a integradora montada; não relê o ambiente. Também aceita substituições (logger, adapter, fakes) para testes.
3. As **três classes** recebem pelo construtor: dependência abstrata (adapter/contrato), **a fatia** de configuração que usam e o logger. A integradora recebe as duas classes (por contrato) e o logger, **sem** configuração de conexão.
4. **Sem singleton global e sem módulo `settings` importável com efeito colateral.** Se houver necessidade de reuso no processo, o ponto de composição guarda a instância e a repassa.
5. **Testes:** `DictSource` com valores fictícios gera `SupabaseSettings` em memória; nada de tocar o ambiente real.
6. A configuração **não** carrega objetos vivos (cliente, conexão); é só dado. O cliente é criado pela Factory a partir dela.

### 8.3 Cenários

- **Teste unitário da classe de arquivos:** cria `DictSource` com bucket e limites, gera as fatias, injeta adapter falso. Sem rede, sem `.env`.
- **Subir em homologação sem `SBX_URL`:** a composição falha ao carregar, com a mensagem da seção 4.2, antes de criar qualquer cliente.
- **Trocar nível de log sem mexer em código:** alterar `SBX_LOG_LEVEL` e reiniciar; como a configuração é imutável, a mudança vale só após novo carregamento. Mudança "a quente" está fora de escopo.
- **Upload acima do limite:** a classe de arquivos compara com `storage.max_file_bytes` antes de chamar o adapter e levanta erro de domínio, sem consumir rede.

## 9. Arquivo modelo de variáveis (só nomes)

- **Local [PROPOSTA]:** `supabase/.env.example` (versionado). O doc 01 (seção 4) pede um modelo só com nomes; este é o mesmo arquivo, evitando dois modelos divergentes.
- **Conteúdo:** uma linha por variável da seção 5, **sem valor** (`NOME=`), agrupada por fatia, com comentário curto indicando obrigatório/opcional, tipo e padrão. Segredos marcados `# SEGREDO`.
- **Fonte da verdade:** a lista de parâmetros fica **definida no código do loader** (futuro) e espelhada na tabela da seção 5. O modelo é gerado/atualizado a partir dela; não editado à mão sem alterar a definição.
- **Manutenção:**
  1. Adicionar parâmetro = atualizar definição, seção 5 deste doc e o `.env.example` na mesma mudança.
  2. **Teste de consistência [PROPOSTA]:** compara os nomes do modelo com os campos do loader; falha se houver nome a mais ou a menos.
  3. O `.env` real continua fora do versionamento (já no `.gitignore`) e nunca é lido para gerar o modelo.
- **Sem sobrescrever o `.env` existente:** o agente que preencher variáveis segue o doc 01 (só acrescenta, não remove nem lê valores).
- **Modelos por ambiente [PROPOSTA]:** um único modelo basta, pois os nomes são iguais nos três ambientes; só os valores diferem e vivem na plataforma de deploy.

## 10. Relação com o doc 01

| Tema | Doc 01 | Este doc |
|---|---|---|
| Obter URL, chaves, buckets, tabelas | Define onde e como obter | Define **nome, tipo, padrão e validação** de cada um |
| Destino dos valores (`.env`) | Seção 4 | Seção 7: `.env` só em dev; demais ambientes via plataforma |
| Reutilizar `SUPABASE_*` ou nomes próprios | Questão 1 (aberta) | Seção 6: análise e recomendação (nomes próprios) |
| Chave pública/secreta | Questão 2 (aberta) | Parâmetros previstos para as duas; só a secreta é obrigatória por padrão |
| Vários ambientes | Questão 3 (aberta) | Seção 7: modelo de ambientes |
| String de conexão Postgres | Questão 4 (aberta) | Opcional e fora do caminho padrão |
| Segurança de segredos | Seção 5 | Mascaramento em `repr`/log e mensagens sem valores (seção 3.1 e 4) |
| Modelo só com nomes | Seção 4 (pedido) | Seção 9: local, conteúdo e manutenção |

**Ajuste sugerido ao doc 01 (a aplicar quando o usuário decidir; este doc não o edita):** o relatório final do agente passa a listar as variáveis pelos **nomes definidos na seção 5** e a conferir contra o `supabase/.env.example`.

## 11. Questões em aberto

| # | Questão | Recomendação |
|---|---|---|
| 1 | Reutilizar `SUPABASE_*` ou nomes próprios? | Nomes próprios (`SBX_*`), fallback legado opcional e desligado. Ver seção 6. |
| 2 | Prefixo definitivo (`SBX_`, `SB_`, `BETTERAI_SUPABASE_`)? | Escolher um curto e sem colisão; `SBX_` é provisório. |
| 3 | A integração usa só a chave secreta ou também a pública? | Só a secreta no backend; pública só se surgir caso de uso com RLS. |
| 4 | Biblioteca para carregar/validar (modelos tipados com validação, ex.: Pydantic Settings, que o projeto talvez já use, ou código próprio com a biblioteca padrão)? | Preferir **sem dependência nova** (biblioteca padrão), para manter a pasta autocontida; reavaliar se o projeto já padroniza Pydantic. Impacta também a questão 4 do doc 00 (modelos tipados). |
| 5 | Um projeto Supabase por ambiente ou um só com separação por schema/bucket? | Um projeto por ambiente (isolamento de dados e chaves). |
| 6 | Valores padrão de limites (50 MiB, página de 50, timeout 10 s) servem? | Validar contra o limite real de upload do projeto e os buckets existentes. |
| 7 | Allowlists obrigatórias em prod? | Sim (menor privilégio). |
| 8 | Aceitar `.env` em homol/prod ou só variáveis da plataforma? | Só plataforma em homol/prod. |
| 9 | Formato de log `json` em prod é desejado? | Sim, se houver coleta de logs; senão manter `pretty` com cor desligada. |

## 12. Critérios de aceite

1. Existe **um único** objeto de configuração, imutável; tentativa de alterar um campo falha.
2. Com variável obrigatória ausente ou vazia, a inicialização falha **antes** de qualquer cliente existir, e a mensagem lista **todas** as ausentes e inválidas.
3. Nenhuma mensagem de erro, `repr`, `str` ou log contém valor de segredo (verificado por teste com valores fictícios reconhecíveis).
4. Cada parâmetro da seção 5 tem teste de: ausência, valor inválido, valor padrão.
5. Nenhuma classe da integração (tabelas, arquivos, integradora, logger, adapter) lê ambiente ou `.env`; só o ponto de composição o faz. Verificável por busca estática de `os.environ`/`getenv` fora do módulo de fonte.
6. Não há variável global/singleton de configuração.
7. Cada classe recebe apenas a sua fatia de configuração.
8. Testes unitários rodam com `DictSource`, sem `.env` e sem rede.
9. Em `prod`, ausência de allowlists ou `SBX_ENV` inválido falha na inicialização.
10. `supabase/.env.example` contém exatamente os nomes da seção 5, sem valores, e o teste de consistência passa.
11. A integração nova inicializa e funciona com as variáveis antigas `SUPABASE_*` presentes e inalteradas no `.env` (coexistência).
12. Mudar `SBX_LOG_LEVEL` e reiniciar altera o nível sem edição de código.

## 13. Referências

Consultadas/indicadas para fundamentar parâmetros (confirmar os valores atuais antes da implementação, pois limites e nomes de chaves mudam):

- Chaves de API (publishable/secret, legadas anon/service_role): <https://supabase.com/docs/guides/api/api-keys>
- Quickstart com Flask (já citado no doc 00/01): <https://supabase.com/docs/guides/getting-started/quickstarts/flask>
- Storage, limites de arquivo e buckets: <https://supabase.com/docs/guides/storage> e <https://supabase.com/docs/guides/storage/uploads/file-limits>
- Storage, URLs assinadas e buckets públicos/privados: <https://supabase.com/docs/guides/storage/serving/downloads>
- Data API (schemas expostos, limite máximo de linhas): <https://supabase.com/docs/guides/api>
- Cliente Python (opções de cliente: schema, timeouts): <https://supabase.com/docs/reference/python/introduction>

> Nota: estas URLs foram indicadas a partir de conhecimento prévio da estrutura da documentação oficial e **não foram abertas nesta sessão**; validar o conteúdo e os links antes de tratá-los como fonte definitiva.
