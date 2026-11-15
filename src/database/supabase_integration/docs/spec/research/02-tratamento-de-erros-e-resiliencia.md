# Tratamento de erros e resiliência

> **Material de pesquisa (refinamento técnico).** A visão geral citada aqui como "00" / "visão geral" agora vive em [../spec.md](../spec.md). As "Questões em aberto" deste arquivo estão **consolidadas e resolvidas em [../decisions.md](../decisions.md)**, que prevalece em caso de divergência. Tarefas de implementação: [../tasks.md](../tasks.md).

> Status: **rascunho de planejamento** (nenhum código escrito). Complementa [spec.md](../spec.md) e [01-variaveis-de-ambiente.md](01-variaveis-de-ambiente.md). Itens marcados como **[PROPOSTA]** são sugestões a validar; decisões pendentes estão em "Questões em aberto". Nomes de classes e exceções são provisórios.

## 1. Contexto e objetivo

A integração tem três classes (tabelas, arquivos, integradora/fachada) sobre um adapter que isola o SDK. Este documento define como as falhas são representadas, classificadas, repetidas e registradas.

Metas:

- O backend nunca vê uma exceção do SDK (`supabase`, `postgrest`, `storage3`, `httpx`). Só vê exceções do domínio.
- Toda falha tem uma classificação clara: recuperável (pode repetir) ou não recuperável.
- Retry e timeout são políticas configuráveis e injetadas, não valores soltos no código.
- Logs de erro trazem contexto útil e nenhum segredo.

Isto reforça a **[PROPOSTA]** da visão geral (seção 3): erros próprios do domínio em vez de vazar exceções do SDK.

## 2. Premissas e pontos a confirmar no SDK instalado

O comportamento exato das exceções muda entre versões do `supabase-py`. Antes de implementar, confirmar na versão fixada no `uv.lock`:

- Operações de tabela (PostgREST) tendem a levantar uma exceção própria com `code`, `message`, `details` e `hint` (formato de erro do PostgREST/PostgreSQL).
- Operações de storage tendem a levantar uma exceção própria com mensagem, `code` e status HTTP. A documentação oficial indica que, em Python, o tratamento é por `try/except` de exceção genérica.
- Falhas de rede e timeout vêm do cliente HTTP subjacente (`httpx`), fora das exceções do Supabase.
- Se a decisão for chamadas diretas (REST) em vez do SDK (questão 1 da visão geral), o mapeamento da seção 5 vale igual, a partir do status HTTP e do corpo JSON.

Regra de design: o adapter **não depende do nome exato** das exceções do SDK para decidir. Ele extrai um "erro bruto normalizado" (ver 5.1) e mapeia a partir de status, `code` e tipo genérico de falha de transporte.

## 3. Hierarquia de exceções do domínio

Módulo previsto: `supabase/errors/` (já sugerido na visão geral). Uma raiz única, uma ramificação por natureza da falha, duas ramificações por frente apenas quando a semântica for específica.

```
SupabaseIntegrationError                 (raiz; nunca levantada diretamente)
├── ConfigurationError                   configuração inválida/ausente
├── ValidationError                      entrada inválida antes de chamar o serviço
├── NotFoundError
│   ├── RecordNotFoundError              registro/linha inexistente
│   └── FileNotFoundInStorageError       objeto inexistente (bucket ou chave)
├── ConflictError
│   ├── DuplicateRecordError             violação de unicidade
│   ├── ReferenceViolationError          violação de chave estrangeira
│   └── FileAlreadyExistsError           objeto já existe e upsert desligado
├── PermissionDeniedError                RLS, política de bucket, chave sem permissão
├── AuthenticationError                  chave/JWT inválido ou expirado
├── PayloadError
│   └── FileTooLargeError                limite de tamanho excedido
├── TimeoutError (nome: OperationTimeoutError)
├── ServiceUnavailableError              rede, 5xx, serviço/pool indisponível
├── RateLimitError                       429 / SlowDown (carrega retry_after)
├── DataError                            SQL/PostgREST rejeitou o dado (tipo, not-null, check)
├── UploadError                          falha de upload não classificável em acima
├── DownloadError                        falha de leitura/download não classificável
└── UnexpectedError                      qualquer exceção não mapeada (fallback)
```

Notas de design:

- **Evitar colidir com `TimeoutError` builtin**: nomear `OperationTimeoutError`.
- **`UploadError` e `DownloadError`** existem porque a visão geral cita "falha de upload". São o destino quando não há causa mais específica; causas específicas (tamanho, permissão, conflito) usam o tipo específico.
- **`UnexpectedError`** é o balde do fallback. Todo erro que cair nele deve gerar log em `ERROR` com a causa original, para que o mapeamento seja ampliado depois.

### 3.1 Atributos comuns (contrato da exceção)

Toda exceção do domínio expõe, sem expor o SDK:

| Atributo | Conteúdo |
|---|---|
| `message` | Texto legível, em português ou neutro, sem segredos |
| `operation` | Nome lógico da operação (ex.: `table.insert`, `storage.upload`) |
| `resource` | Tabela ou bucket (e caminho/chave do objeto, quando aplicável) |
| `retryable` | Booleano derivado da classificação (seção 6) |
| `status` | Status HTTP de origem, quando houver (informativo) |
| `provider_code` | Código bruto do provedor (ex.: `23505`, `PGRST205`, `NoSuchKey`), informativo |
| `attempts` | Quantas tentativas foram feitas até desistir |
| `correlation_id` | Identificador da chamada, para cruzar com logs |
| `__cause__` | A exceção original do SDK, **preservada** via encadeamento (`raise ... from`) |

Decisão importante sobre `__cause__`: manter a causa original encadeada ajuda o diagnóstico em log `DEBUG` e em traceback, mas **o backend não deve importar nem inspecionar tipos do SDK a partir dela**. O contrato público é só o que está na tabela acima. **[PROPOSTA]** documentar isso como regra de revisão de código.

## 4. Onde cada coisa acontece (fronteiras)

| Camada | Pode lançar | Não pode |
|---|---|---|
| Adapter (SDK) | Exceções do domínio, sempre via mapeador | Deixar escapar exceção do SDK/`httpx` |
| Executor de resiliência (timeout, retry, breaker) | Exceções do domínio já mapeadas | Conhecer detalhes de tabela ou storage |
| Classe de tabelas | Exceções do domínio; `ValidationError` para entrada inválida | Capturar e esconder erro sem log; conhecer SDK |
| Classe de arquivos | Exceções do domínio; `ValidationError` para tipo/tamanho | Idem |
| Classe integradora | Propaga as das duas classes | Traduzir, engolir ou reembrulhar com perda de informação |

Fluxo conceitual de uma chamada:

```
backend -> integradora -> tabelas/arquivos -> [executor de resiliência] -> adapter -> SDK
                                                   ^ timeout/retry/breaker      |
                                                   |                            v
                                         mapeador de erros <---------- exceção do SDK
```

O **mapeador de erros** é um componente do adapter, com uma função pura (entrada: erro bruto normalizado; saída: exceção do domínio). Por ser puro, é testável com tabelas de casos sem rede.

## 5. Mapeamento dos erros do SDK para o domínio (dentro do adapter)

### 5.1 Erro bruto normalizado

Primeiro passo do adapter: converter qualquer exceção em um registro interno com `origem` (tabela, storage, transporte), `status`, `code`, `message`, `details`, `hint`. Todo o mapeamento parte desse registro. Isso desacopla a regra das classes concretas do SDK.

### 5.2 Tabelas (PostgREST / PostgreSQL)

Fonte: o PostgREST devolve `code`, `message`, `details`, `hint`; o `code` é um SQLSTATE do PostgreSQL ou um código `PGRSTxxx` do próprio PostgREST, e o status HTTP é derivado do SQLSTATE.

| Condição (code / status) | Exceção do domínio | Recuperável |
|---|---|---|
| `23505` (unicidade), 409 | `DuplicateRecordError` | Não |
| `23503` (chave estrangeira), 409 | `ReferenceViolationError` | Não |
| `23502` (not-null), `23514` (check), `22*` (dado inválido), `PGRST204` (coluna inexistente) | `DataError` | Não |
| `42501` (privilégio insuficiente), 401/403 | `PermissionDeniedError` | Não |
| `PGRST301`, `PGRST302`, `PGRST303`, 401 (JWT) | `AuthenticationError` | Não |
| `42P01`, `PGRST205` (tabela inexistente), `PGRST202` (função inexistente) | `ConfigurationError` (nome de tabela/função errado) | Não (ver nota) |
| `PGRST116` (singular pedido, 0 ou mais de 1 itens) | `RecordNotFoundError` quando 0; `DataError` quando >1 | Não |
| `PGRST000`, `PGRST001`, `PGRST002`, classe `08*`, 503 | `ServiceUnavailableError` | Sim |
| `PGRST003` (timeout aguardando conexão do pool), 504 | `OperationTimeoutError` | Sim |
| `53*` (recursos insuficientes), `57014` (statement timeout) | `ServiceUnavailableError` / `OperationTimeoutError` | Sim, com cautela (ver 7.3) |
| `40001`, `40P01` (serialização / deadlock) | `ServiceUnavailableError` (com `provider_code`) | Sim |
| 429 | `RateLimitError` | Sim |
| Qualquer 5xx não listado | `ServiceUnavailableError` | Sim (somente idempotentes) |
| Qualquer outro 4xx | `DataError` ou `UnexpectedError` | Não |

Notas:

- **"Não encontrado" em tabelas não é erro do PostgREST** para leituras comuns: uma busca por filtro sem linhas devolve lista vazia. Quem decide se vira `RecordNotFoundError` é a classe de tabelas, conforme o contrato do método (ver seção 9 e questão 3).
- **Tabela/coluna inexistente** (`PGRST205`, `PGRST204`, `42P01`) é quase sempre erro de configuração ou schema desatualizado. Pode ser momentaneamente recuperável logo após uma migration (cache de schema do PostgREST desatualizado), mas **[PROPOSTA]** tratar como não recuperável e deixar o log orientar a correção, para não mascarar erro de nome.

### 5.3 Arquivos (Storage)

Fonte: códigos de erro do Storage (corpo `code`/`message` + status HTTP), incluindo os códigos legados (`not_found`, `already_exists`, `unauthorized`, `database_timeout`).

| Condição (code / status) | Exceção do domínio | Recuperável |
|---|---|---|
| `NoSuchKey`, `not_found`, 404 em objeto | `FileNotFoundInStorageError` | Não |
| `NoSuchBucket`, 404 em bucket | `ConfigurationError` (bucket inexistente ou sem acesso) | Não |
| `ResourceAlreadyExists`, `KeyAlreadyExists`, `already_exists`, 409 | `FileAlreadyExistsError` | Não |
| `EntityTooLarge`, 413 | `FileTooLargeError` | Não |
| `InvalidMimeType`, `InvalidKey`, `InvalidBucketName`, `InvalidRequest`, `MissingParameter`, 400 | `ValidationError` | Não |
| `AccessDenied`, `unauthorized`, 403 | `PermissionDeniedError` | Não |
| `InvalidJWT`, `InvalidSignature`, `SignatureDoesNotMatch`, 401 | `AuthenticationError` | Não |
| `InvalidChecksum`, `MissingPart` (integridade do envio) | `UploadError` | Sim para o upload inteiro, se idempotente (ver 7.2) |
| `ResourceLocked`, `LockTimeout`, 423 | `ServiceUnavailableError` (conflito transitório) | Sim |
| `DatabaseTimeout`, `database_timeout`, 504, 544 | `OperationTimeoutError` | Sim |
| `SlowDown`, 429, 503 | `RateLimitError` / `ServiceUnavailableError` | Sim |
| `InternalError`, `DatabaseError`, `internal_server_error`, 500 | `ServiceUnavailableError` | Sim (somente idempotentes) |
| Demais | `UploadError` / `DownloadError` / `UnexpectedError` | Não |

Armadilha documentada pelo próprio Supabase: **404 no Storage pode significar "não existe" ou "existe mas você não tem permissão"**. Por isso, o mapeamento para `FileNotFoundInStorageError` deve manter na mensagem de log a ressalva "ou sem permissão", e o texto da exceção não deve afirmar com certeza que o arquivo não existe. Com a chave de serviço (que ignora RLS), a ambiguidade desaparece na prática. **[PROPOSTA]** registrar em qual chave a chamada rodou (apenas o papel, nunca a chave).

### 5.4 Transporte (rede)

Independente de tabela ou storage:

| Condição | Exceção do domínio | Recuperável |
|---|---|---|
| Timeout de conexão ou de leitura | `OperationTimeoutError` | Sim |
| Falha de conexão, DNS, reset, TLS transitório | `ServiceUnavailableError` | Sim |
| Resposta não decodificável (corpo não JSON, truncado) | `ServiceUnavailableError` ou `UnexpectedError` | Sim, se idempotente |
| Qualquer outra exceção | `UnexpectedError` | Não |

### 5.5 Erros de configuração e entrada (antes de qualquer chamada)

- URL ou chave ausente/malformada, bucket/tabela não configurados: `ConfigurationError`, levantada **na construção** (Factory), não na primeira chamada. Falhar cedo (fail fast).
- Tipo/tamanho de arquivo fora da política, nome de bucket/chave inválido, filtro mal formado: `ValidationError`, **sem ir à rede**.
- A mensagem de `ConfigurationError` cita o **nome** da variável ausente, nunca o valor (coerente com a seção 5 do guia de variáveis).

## 6. Classificação: recuperável x não recuperável

Definição operacional:

- **Recuperável (transitório):** a mesma requisição, repetida depois, pode ter sucesso sem nenhuma mudança de entrada ou de configuração.
- **Não recuperável (permanente):** repetir não ajuda; é necessária correção de entrada, permissão, configuração ou schema.

Regra no código (descrita, não implementada): a **classe da exceção** define o `retryable` padrão. O adapter pode refinar o valor (ex.: `OperationTimeoutError` em operação não idempotente tem `retryable=True` por natureza, mas o executor decide se **pode** repetir; ver seção 7).

| Exceção | `retryable` padrão |
|---|---|
| `ServiceUnavailableError`, `OperationTimeoutError`, `RateLimitError` | Sim |
| `UploadError`/`DownloadError` por integridade (checksum, parte ausente) | Sim |
| `ConfigurationError`, `ValidationError`, `NotFoundError*`, `ConflictError*`, `PermissionDeniedError`, `AuthenticationError`, `PayloadError*`, `DataError` | Não |
| `UnexpectedError` | Não (**[PROPOSTA]**; ampliar o mapeamento em vez de repetir às cegas) |

Dois conceitos distintos que não devem ser confundidos:

1. **`retryable`** (propriedade do erro): "a falha é transitória".
2. **idempotência** (propriedade da operação): "repetir não causa efeito duplicado".

Só se repete quando **os dois** forem verdadeiros (ou quando houver chave de idempotência, ver 7.2).

## 7. Retry com backoff exponencial e jitter

### 7.1 Política (configurável, injetada)

Objeto de política imutável, injetado no executor de resiliência (DI), com valores padrão **[PROPOSTA]**:

| Parâmetro | Padrão sugerido | Observação |
|---|---|---|
| `max_attempts` | 3 (total, incluindo a primeira) | 1 = sem retry |
| `base_delay` | 0,5 s | |
| `multiplier` | 2 | |
| `max_delay` | 8 s | teto por espera |
| `jitter` | "full jitter": espera sorteada em [0, atraso_exponencial] | evita rajadas sincronizadas (thundering herd) |
| `retry_budget` (tempo total) | 30 s para tabelas, 120 s para uploads grandes | teto absoluto, independente do nº de tentativas |
| `respect_retry_after` | sim | para `RateLimitError` com `retry_after`, usa o maior entre o backoff e o valor informado |

Fórmula conceitual: `espera_n = aleatório(0, min(max_delay, base_delay * multiplier^(n-1)))`. O gerador aleatório e o relógio (`sleep`) são **injetáveis**, para testes determinísticos sem esperar de verdade.

Os parâmetros vêm de variáveis de ambiente com prefixo próprio (nomes a definir junto com o guia de variáveis, questão 1 de lá), com defaults seguros. **[PROPOSTA]** permitir sobrescrita por operação (ex.: upload com orçamento maior).

### 7.2 Quais operações podem repetir

Premissa: o cliente HTTP do SDK não envia chave de idempotência por padrão. Logo, a idempotência é uma propriedade do **tipo de operação** e dos **dados**.

| Operação | Idempotente? | Repetir após falha transitória? |
|---|---|---|
| Buscar por id / por filtros / listar (tabela) | Sim (leitura) | **Sim** |
| Download, URL assinada, listagem de arquivos | Sim (leitura) | **Sim** |
| Verificar existência | Sim | **Sim** |
| Atualizar por chave (`UPDATE ... WHERE id = x` com valores absolutos) | Sim (mesmo resultado se repetido) | **Sim** |
| Atualizar com valor relativo (`contador = contador + 1`, via RPC) | Não | **Não** |
| Deletar por chave (tabela) | Sim quanto ao estado final | **Sim**; "já inexistente" na repetição é sucesso (ver nota) |
| Deletar arquivo | Sim quanto ao estado final | **Sim**; idem |
| Upsert (tabela) por chave de conflito | Sim | **Sim** |
| Upload com `upsert=true` (sobrescreve) | Sim (mesmo conteúdo/chave final) | **Sim** |
| Upload com `upsert=false` | Não: se a 1ª tentativa chegou ao servidor e a resposta se perdeu, a 2ª dá conflito 409 | **Não automaticamente** (ver tratamento abaixo) |
| Inserir registro (`INSERT`) sem chave natural | Não: pode duplicar | **Não** |
| Inserir com id gerado pelo cliente (UUID) + restrição de unicidade | Efetivamente sim, se tratar `23505` como "já gravado" | **Sim, com cuidado** (ver abaixo) |
| Inserção em lote | Não (parcial/duplicação) | **Não**, salvo lote idempotente por chave (upsert em lote) |
| Chamadas de função/RPC arbitrárias | Desconhecido | **Não**, a menos que o chamador declare idempotência |

Tratamentos específicos:

- **Deletar e "não encontrado" na repetição:** se a 1ª tentativa deu timeout e a 2ª devolveu "não existe", o objetivo (o item não existir) foi cumprido. **[PROPOSTA]** a classe converte `NotFound` em sucesso apenas **quando a operação já foi tentada e falhou por erro transitório** (flag interna `retried`). Na primeira tentativa, `NotFound` continua sendo exceção (ou retorno "não removido", conforme contrato; questão 3).
- **Insert com UUID do cliente:** repetir após timeout pode dar `23505`. Se a chave primária é a mesma da tentativa anterior, tratar como sucesso silencioso é perigoso (pode ser outro registro com mesmo id por bug). **[PROPOSTA]** só habilitar esse comportamento por opção explícita do chamador (`idempotency_key`/"id determinístico"), nunca por padrão.
- **Upload sem upsert:** na falha transitória, antes de repetir ou desistir, **conferir por leitura** (existe o objeto? mesmo tamanho?). Se existir e bater, tratar como sucesso; senão, repetir. Isso é uma "reconciliação", não um retry cego. **[PROPOSTA]** disponível como estratégia opcional; padrão: não repetir e propagar o erro.
- **Fluxo de upload com fluxo de dados (stream/arquivo aberto):** só repetir se a fonte puder ser relida do início (bytes em memória ou arquivo reabrível). Fonte consumida de forma não reiniciável: `retryable` efetivo = não.

### 7.3 Cuidados adicionais

- **Timeout não prova que a operação não ocorreu.** Em escrita não idempotente, o timeout é o pior caso (resultado incerto). O erro propagado deve indicar isso: `OperationTimeoutError` com `outcome_unknown=True` **[PROPOSTA]** para o backend decidir (reconciliar, alertar).
- **`57014` (statement timeout) e `PGRST003`:** repetir uma consulta pesada tende a repetir o problema e agravar a carga. **[PROPOSTA]** limitar a no máximo 1 retry para esses códigos e alertar em log `WARNING`.
- **Rate limit:** respeitar `Retry-After` quando disponível; nunca repetir imediatamente.
- **Não repetir sobre repetição:** o retry vive em **um único lugar** (o executor de resiliência no adapter). Camadas acima (tabelas, arquivos, integradora) **não** implementam retry próprio, para não multiplicar tentativas (3 x 3 = 9).
- **Concorrência e carga:** em lotes grandes, o retry com jitter + o teto de tempo evitam tempestade de requisições contra um serviço já degradado.

## 8. Política de timeout

### 8.1 Princípios

- **Todo** acesso de rede tem timeout explícito. Nunca depender do padrão do cliente HTTP (que pode ser longo ou inexistente, conforme a versão).
- O timeout é **por tentativa**; o `retry_budget` (7.1) é o teto **total** da operação.
- Timeouts separados por fase, quando o cliente HTTP permitir: **conexão** (curto), **leitura/resposta** (varia por tipo de operação), e opcionalmente **escrita** para uploads.

### 8.2 Valores padrão sugeridos **[PROPOSTA]** (todos configuráveis)

| Tipo de operação | Conexão | Leitura/resposta | Observação |
|---|---|---|---|
| CRUD de tabela (1 registro) | 3 s | 10 s | |
| Listagem/busca com paginação | 3 s | 20 s | limitar tamanho de página protege o tempo |
| Operação em lote (tabela) | 3 s | 60 s | |
| Download de arquivo | 3 s | proporcional ao tamanho, com teto (ex.: 120 s) | |
| Upload de arquivo | 3 s | proporcional ao tamanho, com teto (ex.: 300 s) | |
| URL assinada, listagem de arquivos, delete | 3 s | 10 s | |

Para arquivos, o ideal é um timeout **por inatividade** (sem progresso) em vez de um tempo fixo, pois arquivos grandes demoram legitimamente. Se o cliente HTTP só oferecer timeouts fixos, derivar do tamanho conhecido (`base + tamanho / vazão_mínima_esperada`). **[PROPOSTA]**; ver questão 5.

### 8.3 Relação com os limites do servidor

O servidor também tem limites (timeout de instrução no banco; limites de tamanho de arquivo configuráveis no projeto; erros `DatabaseTimeout`/504). O timeout do cliente deve ser **menor ou igual** ao do servidor para que a falha seja controlada pelo cliente e classificada como `OperationTimeoutError`, em vez de depender de um 5xx. Confirmar os limites reais do projeto na plataforma (somente leitura, conforme o guia de variáveis).

## 9. Circuit breaker: vale a pena?

### 9.1 Avaliação

| Argumento a favor | Argumento contra |
|---|---|
| Evita martelar um Supabase fora do ar e acumular requisições penduradas | O consumidor é um backend de um serviço só, com tráfego moderado; o ganho é menor que em microsserviços de alto volume |
| Falha rápida protege threads/event loop e a latência do restante do backend | Estado compartilhado entre workers (vários processos Uvicorn) exige decisão: breaker por processo é simples, mas impreciso |
| Combina bem com retry: o retry cuida de falhas curtas, o breaker de falhas longas | Complexidade extra (estados, limiares, testes) e risco de falso positivo bloqueando operações saudáveis (ex.: um bucket com problema derrubando as tabelas) |
| Facilita degradação elegante (o backend pode responder "indisponível" rápido) | Os timeouts e o `retry_budget` já limitam o pior caso por chamada |

### 9.2 Recomendação

**Não incluir na primeira versão (MVP); desenhar o ponto de extensão.** Justificativa: timeouts rigorosos + retry limitado já impedem o travamento; o breaker traz valor real só com tráfego alto ou falhas prolongadas observadas.

O ponto de extensão custa pouco: o executor de resiliência recebe uma **cadeia de políticas** (timeout, retry, e opcionalmente breaker) como dependências injetadas. Adicionar um breaker depois é um novo item na cadeia, sem alterar as três classes (princípio aberto/fechado).

Se for incluído em fase posterior **[PROPOSTA]**:

- Um breaker **por frente** (um para tabelas, outro para storage), nunca um só global, pois as falhas são independentes.
- Contabilizar apenas falhas **transitórias** (`ServiceUnavailableError`, `OperationTimeoutError`); erros de domínio (`NotFound`, `Conflict`, `Permission`, `Validation`) **não** abrem o circuito.
- Estados: fechado, aberto (falha rápida com `CircuitOpenError`, subclasse de `ServiceUnavailableError`, com `retryable=False` durante o período aberto), semiaberto (sonda limitada).
- Limiar, janela e tempo de abertura configuráveis; estado exposto em log e, se existir, num health check.
- Critério para adotar: observar em produção/homologação picos de lentidão ou indisponibilidade do Supabase que causem acúmulo de chamadas penduradas.

## 10. Relação entre erros e logs

Integra-se ao padrão da seção 3.2 da visão geral (nível configurável, cores, campos organizados, logger injetado, sem segredos).

### 10.1 Níveis

| Situação | Nível | Observação |
|---|---|---|
| Chamada bem-sucedida | `INFO` ou `DEBUG` (conforme verbosidade configurada) | duração e resultado resumido |
| Tentativa falhou e será repetida | `WARNING` | inclui nº da tentativa, espera até a próxima, causa resumida |
| Erro de domínio esperado, sem repetição (ex.: `NotFound`, `Conflict` em fluxo normal) | `INFO` ou `WARNING` | **[PROPOSTA]**: não usar `ERROR` para resultados que o backend trata como fluxo normal |
| Falha definitiva (desistiu após tentativas, não recuperável inesperada, `PermissionDenied`, `Authentication`, `Configuration`) | `ERROR` | |
| `UnexpectedError` | `ERROR` com detalhe extra em `DEBUG` (tipo original, traceback) | sinal para ampliar o mapeamento |
| Início/fim de cada tentativa, payload resumido, parâmetros de política | `DEBUG` | |
| Circuito aberto (se existir) | `WARNING` na abertura/fechamento; `DEBUG` nas rejeições rápidas | evita enxurrada de logs |

Regra de ouro: **registrar cada erro uma única vez, na fronteira que o trata**. O adapter registra a tentativa e o mapeamento; as classes de tabelas/arquivos registram o resultado final da operação; a integradora **não** registra de novo o que já foi registrado abaixo (evita logs duplicados em cascata). Quem captura e trata o erro no backend registra o que for do seu contexto.

### 10.2 Campos de contexto (estruturados)

Por evento de erro: `operation`, `resource` (tabela/bucket + caminho), `attempt`/`max_attempts`, `elapsed_ms`, `status`, `provider_code`, `exception_class` (nome da exceção do domínio), `retryable`, `correlation_id`, `outcome_unknown` quando aplicável. Para a causa original, registrar **somente o tipo e a mensagem sanitizada**; traceback completo apenas em `DEBUG`.

### 10.3 O que nunca vai para o log ou para a mensagem da exceção

- Chaves (`service_role`/secret, anon/publishable), JWTs, cabeçalhos `Authorization`/`apikey`, URLs assinadas completas (contêm token), senhas ou strings de conexão.
- Conteúdo de arquivos e valores de colunas de registros (podem ser dados pessoais). Registrar identificadores e **nomes** de colunas, contagens e tamanhos, nunca os valores.
- A URL do projeto pode ser registrada de forma reduzida (host) apenas em `DEBUG`; **[PROPOSTA]** não registrá-la em níveis superiores.

Implementação conceitual: um **sanitizador** único (função pura) aplicado a mensagem, `details`, `hint` e à causa antes de qualquer log ou antes de preencher a exceção do domínio. Atenção especial: o `details` do PostgreSQL pode conter o valor da linha ("Failing row contains (...)", como no exemplo oficial do PostgREST) e o `message` pode citar valores; por isso o sanitizador deve **truncar ou remover** esses trechos. Testes devem incluir "segredo plantado" que não pode aparecer na saída.

### 10.4 Cores

A cor segue o nível (definida no módulo de logs, doc próprio). Para erros: `ERROR` com a cor de destaque, `WARNING` para tentativa repetida. Não carregar significado só na cor (o nível textual sempre presente), para funcionar com a saída redirecionada para arquivo/terminal sem cor.

## 11. O que cada uma das três classes propaga

### 11.1 Adapter / executor de resiliência (apoio)

- Aplica timeout, retry e (futuramente) breaker; mapeia exceções do SDK para o domínio; sanitiza; registra tentativas.
- **Propaga:** somente exceções do domínio, com `__cause__` preservado e `attempts` preenchido.

### 11.2 Classe de tabelas

- Valida entrada e levanta `ValidationError` antes de ir à rede.
- Decide a semântica de "não encontrado" por método **[PROPOSTA]**:
  - `get_by_id`: levanta `RecordNotFoundError` se não houver registro (ou, se preferido, retorna `None`; questão 3).
  - `find`/`list`: lista vazia nunca é erro.
  - `update`/`delete` por id: 0 linhas afetadas levanta `RecordNotFoundError` (a menos que o contrato de delete seja "idempotente por resultado"; questão 3).
- Declara ao executor a **idempotência** de cada método (ex.: `insert` = não idempotente; `upsert` = idempotente), conforme a tabela 7.2.
- **Propaga:** `ValidationError`, `RecordNotFoundError`, `DuplicateRecordError`, `ReferenceViolationError`, `DataError`, `PermissionDeniedError`, `AuthenticationError`, `ConfigurationError`, `OperationTimeoutError`, `ServiceUnavailableError`, `RateLimitError`, `UnexpectedError`. **Não** propaga exceções de arquivo.

### 11.3 Classe de arquivos

- Valida bucket, chave (caminho), tipo e tamanho antes do upload (`ValidationError`, `FileTooLargeError`).
- Declara idempotência: `upload` com upsert = idempotente; sem upsert = não; `download`/`list`/`signed_url` = idempotentes; `delete` = idempotente por resultado.
- **Propaga:** `ValidationError`, `FileNotFoundInStorageError`, `FileAlreadyExistsError`, `FileTooLargeError`, `PermissionDeniedError`, `AuthenticationError`, `ConfigurationError` (bucket inexistente), `UploadError`, `DownloadError`, `OperationTimeoutError`, `ServiceUnavailableError`, `RateLimitError`, `UnexpectedError`. **Não** propaga exceções de registro.
- Em falha de upload com resultado incerto, indicar `outcome_unknown` para o backend poder conferir o objeto.

### 11.4 Classe integradora (fachada)

- Compõe e delega. **Não captura, não traduz, não engole** erros das duas classes; propaga o mesmo objeto de exceção.
- Operações que combinam as duas frentes (se existirem, ex.: salvar arquivo e gravar a referência na tabela) **não são transacionais** (Supabase não oferece transação entre Storage e Postgres via API). **[PROPOSTA]** a integradora **não** terá compensação automática no MVP: se o passo 2 falhar após o passo 1, propaga a exceção do passo 2 enriquecida com o contexto "passo 1 concluído" (`partial_success`), e o backend decide limpar (ex.: apagar o arquivo órfão). A ausência de compensação automática precisa ser decisão explícita (questão 4).
- Inicialização: validação da configuração via Factory; falha vira `ConfigurationError` na criação.

## 12. Exemplos de cenários

| # | Cenário | Resultado esperado |
|---|---|---|
| 1 | Busca por id inexistente (`get_by_id`) | `RecordNotFoundError` (ou `None`, conforme decisão), log `INFO`, **sem retry** |
| 2 | Insert viola unicidade (`23505`) | `DuplicateRecordError`, `retryable=False`, log `WARNING`, sem retry |
| 3 | Leitura com timeout na 1ª e 2ª tentativas, sucesso na 3ª | Retorna o resultado; 2 logs `WARNING` com espera crescente e jitter; 1 log de sucesso com `attempts=3` |
| 4 | Leitura com timeout nas 3 tentativas | `OperationTimeoutError(attempts=3, retryable=True)`; 1 log `ERROR` final; `__cause__` preservado |
| 5 | Insert simples dá timeout | **Sem retry**; `OperationTimeoutError` com `outcome_unknown=True`; log `ERROR` |
| 6 | Upload de 200 MB acima do limite do projeto (413) | `FileTooLargeError`, sem retry; se houver limite local, falha antes de ir à rede com `ValidationError`/`FileTooLargeError` |
| 7 | Upload com `upsert=true` falha com 503 e depois funciona | Retry automático; um único objeto final |
| 8 | Upload sem upsert recebe 409 | `FileAlreadyExistsError`, sem retry |
| 9 | Download de objeto inexistente | `FileNotFoundInStorageError`; mensagem não afirma ausência definitiva (pode ser permissão) |
| 10 | Chave inválida/expirada (401) | `AuthenticationError`, log `ERROR`, **sem retry**; mensagem não contém a chave |
| 11 | RLS bloqueia a escrita (`42501`/403) | `PermissionDeniedError`, sem retry; log orienta a revisar políticas/chave |
| 12 | Resposta 429 com `Retry-After` | `RateLimitError`; espera o maior entre backoff e `Retry-After`; retry dentro do orçamento |
| 13 | Variável de URL ausente na inicialização | `ConfigurationError` citando o **nome** da variável; falha na Factory |
| 14 | Exceção desconhecida do SDK | `UnexpectedError` com `__cause__`; log `ERROR` + `DEBUG` com tipo original |
| 15 | Fachada: arquivo salvo, gravação da referência falha | Propaga a exceção da tabela com `partial_success`; backend decide limpar o arquivo |
| 16 | Delete após timeout: 2ª tentativa devolve "não existe" | Tratado como sucesso (estado final alcançado), com log `INFO` explicando |

## 13. Estratégia de testes (resumo) **[PROPOSTA]**

- **Mapeador de erros:** testes de tabela (entrada: erro bruto normalizado; saída: exceção + `retryable`), cobrindo todos os códigos das seções 5.2 a 5.4 e o caso "desconhecido".
- **Retry/backoff:** com relógio e gerador aleatório falsos; verificar nº de tentativas, teto de espera, teto de tempo total e que **operações não idempotentes não repetem**.
- **Timeout:** cliente HTTP falso que atrasa; verificar `OperationTimeoutError` e `outcome_unknown` em escrita.
- **Sanitização:** segredo plantado em mensagem, `details`, URL e cabeçalho nunca aparece no log nem na exceção.
- **Fachada:** garantir que não reembrulha exceções (mesmo objeto, mesma identidade) e que `partial_success` é preenchido.
- **Isolamento:** teste de arquitetura simples garantindo que nada fora do adapter importa o SDK, e que nenhuma exceção do SDK escapa da fronteira.

## 14. Critérios de aceite

1. Nenhum módulo fora do adapter importa o SDK ou `httpx`; nenhuma exceção desses pacotes alcança o backend (verificado por teste).
2. Existe a hierarquia da seção 3 com os atributos comuns da seção 3.1 e `__cause__` preservado.
3. O mapeamento cobre ao menos os códigos listados em 5.2, 5.3 e 5.4, e todo erro não mapeado resulta em `UnexpectedError` (nunca em exceção do SDK).
4. Toda chamada de rede tem timeout explícito, configurável; o `retry_budget` limita o tempo total.
5. Retry usa backoff exponencial com jitter, é injetável e **só** repete operações idempotentes com erro `retryable`; existe teste provando que `insert` simples e inserção em lote não repetem.
6. O retry existe em um único lugar (executor de resiliência), não nas três classes.
7. Logs de erro respeitam os níveis da seção 10.1, trazem os campos da 10.2 e passam no teste de "segredo plantado" (10.3).
8. A fachada propaga exceções sem traduzi-las; o comportamento de operações combinadas está documentado e testado.
9. O circuito aberto está **fora** do MVP, mas o ponto de extensão (cadeia de políticas injetável) está presente e documentado.
10. Erros de configuração falham na criação (Factory) e citam apenas nomes de variáveis.

## 15. Questões em aberto

1. **SDK ou REST direto?** (herdada da visão geral) Define quais exceções o adapter precisa interceptar. *Recomendação:* usar o SDK oficial atrás do adapter e manter o mapeamento baseado em status/`code` normalizados (5.1), assim a troca para REST direto não afeta o domínio.
2. **Síncrono ou assíncrono?** Afeta o executor de resiliência (espera com `sleep` bloqueante x assíncrona) e o cancelamento por timeout. *Recomendação:* decidir junto com a questão 2 da visão geral; desenhar o executor com a mesma interface lógica nos dois modos.
3. **Semântica de "não encontrado":** `get_by_id` lança exceção ou devolve `None`? `delete` de item inexistente é erro ou sucesso? *Recomendação:* `get_by_id` lança `RecordNotFoundError` (falha explícita); `find`/`list` devolvem vazio; `delete` idempotente por resultado (inexistente = sucesso), com o resultado indicando se algo foi removido de fato.
4. **Operações combinadas (arquivo + registro):** aceitar ausência de compensação automática no MVP? *Recomendação:* sim, propagar `partial_success` e deixar o backend decidir; reavaliar compensação (sagas simples) quando houver caso de uso real.
5. **Limites de tamanho/tipo e timeouts de upload:** quais os limites de arquivo reais do projeto e há necessidade de upload resumível para arquivos grandes? *Recomendação:* levantar os limites na plataforma (somente leitura), validar localmente antes do upload e adiar upload resumível até haver arquivos que justifiquem.
6. **Idempotência de inserts:** haverá ids gerados no cliente (UUID) ou chaves naturais nas primeiras tabelas? *Recomendação:* preferir `upsert` por chave natural/UUID nos casos de uso que precisam de retry; manter `insert` sem retry por padrão.
7. **Circuit breaker:** confirmar a recomendação de deixar fora do MVP. *Recomendação:* sim, com ponto de extensão e critério de adoção (9.2).
8. **Valores padrão de timeout/retry:** os números das seções 7.1 e 8.2 são palpites razoáveis. *Recomendação:* aceitar como ponto de partida e calibrar com medições reais em homologação.
9. **Nomes das variáveis de política** (timeouts, tentativas) e o prefixo: depende da decisão da questão 1 do guia de variáveis (reaproveitar nomes `SUPABASE_*` ou nomes próprios). *Recomendação:* nomes próprios e isolados, para não interferir na integração antiga.
10. **Informar `outcome_unknown` ao backend:** aceitar este atributo como parte do contrato público? *Recomendação:* sim; é a única forma de o backend lidar corretamente com timeout em escrita.

## 16. Referências

Consultadas para este documento:

- Supabase, tratamento e códigos de erro do Storage (inclui exemplo de `try/except` em Python, códigos novos e legados, `SlowDown`, `EntityTooLarge`, ambiguidade 404/permissão): <https://supabase.com/docs/guides/storage/debugging/error-codes>
- PostgREST, referência de erros (estrutura `code`/`message`/`details`/`hint`, mapeamento SQLSTATE para HTTP, códigos `PGRST*`, cabeçalho `Proxy-Status`): <https://postgrest.org/en/stable/references/errors.html> (redireciona para <https://docs.postgrest.org/en/stable/references/errors.html>)

Do planejamento do projeto:

- [spec.md](../spec.md)
- [01-variaveis-de-ambiente.md](01-variaveis-de-ambiente.md)

Pendentes de consulta na etapa de implementação (não consultadas aqui): classes de exceção exatas do `supabase-py`/`postgrest-py`/`storage3` na versão fixada no `uv.lock`; opções de timeout do cliente HTTP usado pelo SDK; limites de arquivo e de timeout de instrução do projeto na plataforma.
