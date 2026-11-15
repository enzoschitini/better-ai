# Operações em lote e paginação

> **Material de pesquisa (refinamento técnico).** A visão geral citada aqui como "00" / "visão geral" agora vive em [../spec.md](../spec.md). As "Questões em aberto" deste arquivo estão **consolidadas e resolvidas em [../decisions.md](../decisions.md)**, que prevalece em caso de divergência. Tarefas de implementação: [../tasks.md](../tasks.md).

> Status: **rascunho de planejamento** (nenhum código escrito). Itens marcados como **[PROPOSTA]** são sugestões a validar; decisões pendentes estão em "Questões em aberto".
> Complementa [spec.md](../spec.md) e [01-variaveis-de-ambiente.md](01-variaveis-de-ambiente.md). Vale para a classe de tabelas (e, na seção 9, para a de arquivos). Nada aqui importa ou se baseia na integração Supabase antiga.

## 1. Contexto e objetivo

O backend precisará gravar e ler volumes que não cabem numa única chamada (importações, reprocessamentos, varreduras). Este documento define como a integração trata:

- escrita em lote (insert, update, upsert, delete);
- listagem paginada (offset x keyset), ordenação, contagem;
- iteração preguiçosa de tabelas grandes;
- respeito aos limites do servidor;
- paginação de objetos do Storage;
- interação com timeouts, retry e logs.

O backend nunca deve precisar saber de `range`, `Range` headers ou limites do PostgREST: isso fica no adapter.

## 2. Limites do servidor (fatos e premissas)

| Item | Valor / comportamento | Fonte / status |
|---|---|---|
| Máximo de linhas por resposta | Projetos Supabase retornam no máximo **1.000 linhas** por padrão; configurável nas configurações da API do projeto (`max-rows`) | Doc oficial do Supabase (referência `select`) |
| Paginação nativa | `range(from, to)` (índices inclusivos) e `limit` | Doc oficial; sintaxe detalhada **a confirmar** |
| Contagem | Parâmetro `count` aceita `exact`, `planned`, `estimated` | Doc do PostgREST; a página do Supabase consultada só exemplifica `exact`. **A confirmar** |
| Storage `list` | `limit` padrão **100**; opções `offset`, `sortBy`, `search` | Doc oficial do Supabase Storage |
| Storage `listV2` (cursor) | Citado no menu da referência JS; parâmetros **não verificados** | **A confirmar** |
| Upsert | `on_conflict`, `ignore_duplicates`, `returning` (`minimal`/`representation`), `default_to_null` (só em upsert em lote) | Doc oficial (referência Python `upsert`) |

Não encontrei na documentação consultada um limite oficial de linhas por INSERT em lote; o limite prático vem de tamanho de payload, timeout da requisição e `statement_timeout` do banco. **[PROPOSTA]** tratar o tamanho de lote como configuração, com padrão conservador.

Princípio: **a integração nunca assume que o servidor devolve tudo que foi pedido.** Se o usuário pede 5.000 itens e o `max-rows` é 1.000, a integração pagina internamente ou falha de forma explícita, jamais trunca em silêncio.

## 3. Operações em lote

### 3.1 Divisão em chunks

- Entrada: sequência de registros (lista ou iterável).
- A integração divide em chunks de tamanho `batch_size`.
- **[PROPOSTA]** `batch_size` padrão **500** para insert/upsert e **200** para update/delete por lista de ids (URLs com `in.(...)` crescem com o nº de ids). Configurável por variável de ambiente e por chamada.
- Limite superior duro (**[PROPOSTA]** 1.000, alinhado ao `max-rows` padrão, pois com `returning=representation` a resposta é limitada por ele). Valor acima do teto: erro de validação, não ajuste silencioso.
- Chunks podem ser limitados também por bytes estimados (**[PROPOSTA]** opcional, `max_batch_bytes`).
- Execução **sequencial por padrão**; concorrência limitada (`max_concurrency`) é opcional e fica fora da primeira versão **[PROPOSTA]**.

### 3.2 Semântica: parcial x tudo-ou-nada

Cada chunk é uma única requisição, logo **atômico** no Postgres (ou todas as linhas do chunk entram, ou nenhuma). Entre chunks não há atomicidade. Dois modos, escolhidos por parâmetro `on_error`:

| Modo | Comportamento | Quando usar |
|---|---|---|
| `stop` (padrão **[PROPOSTA]**) | Para no primeiro chunk com falha; chunks anteriores permanecem gravados; relatório indica o ponto de parada | Cargas onde ordem importa ou falha indica problema sistêmico |
| `continue` | Registra a falha do chunk e segue; relatório final lista chunks falhos | Cargas idempotentes (upsert) onde se quer o máximo possível |

**Tudo-ou-nada real** (atomicidade entre chunks) exige transação no banco, algo que o PostgREST não oferece entre requisições. Opções:

1. Usar **um único chunk** (limitado ao teto acima): atomicidade garantida.
2. Função RPC no Postgres que receba o lote inteiro (fora do escopo, pois exige DDL; ver visão geral, seção 5).

Recomendação: documentar que o lote **multi-chunk não é atômico**; oferecer `atomic=True` que só aceita se couber em um chunk e, caso contrário, falha antes de enviar qualquer coisa.

### 3.3 Falha dentro de um chunk e isolamento de item

Como o chunk é atômico, um registro inválido derruba o chunk inteiro. Estratégia **[PROPOSTA]** `isolate_failures` (desligada por padrão): ao falhar um chunk por erro de dados (não de rede), reenvia por **bisseção** (divide o chunk ao meio recursivamente) até identificar os itens ruins. Custo: mais requisições; só vale em `continue`. Erros transitórios (rede, 5xx, timeout) não disparam bisseção, e sim retry (seção 8).

### 3.4 Relatório de resultado por item

Todo método de lote devolve um **BatchResult** (não lança exceção por falha parcial em `continue`):

- `total_items`, `succeeded`, `failed`, `skipped`;
- `chunks_total`, `chunks_ok`, `chunks_failed`, `duration`;
- `items`: lista de **ItemOutcome** em ordem da entrada com `index` (posição original), `status` (`ok`/`failed`/`skipped`), `record` opcional (se `returning=representation`), `error` opcional (erro de domínio, sem segredos);
- `aborted`: booleano (parou em `stop`).

Observações:
- Com `returning=minimal` o servidor não devolve linhas, então `record` fica vazio; o status por item é inferido do status do chunk. **[PROPOSTA]** padrão `minimal` em lotes grandes (menos tráfego e menos limite de `max-rows`), `representation` sob pedido.
- Em `ignore_duplicates`, o servidor não diz quais itens foram ignorados; o relatório só distingue por contagem (`count`) quando disponível. Documentar a limitação; não fingir granularidade.
- O relatório de erro mapeia exceções do SDK para erros do domínio (ver visão geral, seção 3).

### 3.5 Operações

| Operação | Contrato (pseudo-assinatura) | Notas |
|---|---|---|
| Insert em lote | `insert_many(table, records, *, batch_size, on_error, returning) -> BatchResult` | Registros devem ter o mesmo conjunto de chaves por chunk, ou o adapter normaliza (ver `default_to_null`) |
| Upsert em lote | `upsert_many(table, records, *, on_conflict, ignore_duplicates, batch_size, on_error, returning) -> BatchResult` | `on_conflict` obrigatório quando a chave não for a primária; **idempotente**, portanto o modo ideal para retry de lotes |
| Update em lote | ver abaixo | Dois casos distintos |
| Delete em lote | `delete_many(table, ids_or_filter, *, id_column, batch_size, on_error) -> BatchResult` | Por lista de ids em chunks; ou por filtro (uma requisição, sem chunks) |

Update em lote tem duas formas, que **não** devem ser misturadas no mesmo método:
- **Mesmo valor para N linhas:** `update_where(table, values, filter) -> UpdateResult` (uma requisição; devolve contagem afetada).
- **Valores diferentes por linha:** `update_many(table, [(id, values), ...])`. PostgREST não tem "update em massa com valores distintos"; a implementação deve usar **upsert** pela chave primária (exige enviar a linha completa ou colunas NOT NULL cobertas) ou N updates individuais. **[PROPOSTA]** upsert por PK quando possível, documentando a restrição; senão, updates individuais em `continue`.

### 3.6 Proteções **[PROPOSTA]**

- `delete_where` e `update_where` **sem filtro** são recusados (erro de validação), exceto com flag explícita `allow_unfiltered=True`.
- Opção `dry_run=True` em lotes: valida, divide em chunks e loga o plano, sem enviar.
- Ids duplicados na entrada de um upsert no mesmo chunk causam erro no Postgres ("cannot affect row a second time"): a integração **deduplica por chave dentro do chunk** (último vence) e informa no relatório.

## 4. Paginação de listagens

### 4.1 Offset/limit x keyset (cursor)

| Critério | Offset/limit (`range`) | Keyset (cursor) |
|---|---|---|
| Simplicidade | Alta | Média |
| Acesso aleatório ("página 7") | Sim | Não |
| Custo em páginas profundas | Cresce (banco descarta N linhas) | Constante com índice |
| Estabilidade sob escrita concorrente | Ruim (linhas puladas ou repetidas) | Boa |
| Exige ordenação estável e única | Sim, para ser determinístico | Sim, obrigatoriamente |
| Ordenação por colunas não indexadas | Funciona (lento) | Lento também; exige índice |
| Total de páginas | Fácil com contagem | Não natural |

**Recomendação [PROPOSTA]:**
- **Keyset como padrão** para varreduras, iteração e listagens grandes.
- **Offset** disponível para telas com "ir para página N" e tabelas pequenas; a integração loga aviso quando `offset` passa de um limiar (**[PROPOSTA]** 10.000).
- A API pública expõe um único método `list(...)` com `pagination=keyset|offset`.

### 4.2 Ordenação estável

- Toda listagem paginada exige `order_by`. Sem ele, a integração aplica a **chave primária ascendente** (configurável por tabela) ou recusa se não conhecer a PK.
- Ordenação deve terminar numa **coluna única** (desempate). Ex.: `created_at desc, id desc`. Se a lista informada não incluir a PK, a integração **acrescenta a PK como último critério**.
- Valores `NULL` na ordenação: explicitar `nulls_first/nulls_last`; o keyset com colunas anuláveis é complexo. **[PROPOSTA]** na v1, keyset só com colunas de ordenação **NOT NULL** (validação no início; caso contrário erro claro ou fallback para offset com aviso).

### 4.3 Keyset: formato do cursor

- Cursor **opaco** para o consumidor (string codificada) contendo: valores da última linha para as colunas de ordenação, direção e uma versão do formato. Não contém segredos nem registros completos.
- **[PROPOSTA]** Cursor atrelado a uma "assinatura" da consulta (tabela, filtros, ordenação); se o consumidor reutilizar um cursor com consulta diferente, erro de validação.
- Condição de avanço para ordenação composta `(a, b)`: linhas "depois" de `(a0, b0)`; o adapter traduz para filtro composto equivalente (ex.: `a > a0 OR (a = a0 AND b > b0)`), pois o PostgREST não tem comparação de tupla nativa. Documentar isso como ponto de atenção na implementação.

### 4.4 Contagem total

| Modo | O que faz | Custo / precisão |
|---|---|---|
| `exact` | `COUNT(*)` real | Preciso; custo cresce com o tamanho da tabela e do filtro (varredura) |
| `planned` | Estimativa do planejador (EXPLAIN) | Barato; pode estar bem errado, depende de estatísticas atualizadas |
| `estimated` | `exact` até um limiar, depois `planned` | Meio-termo |
| (nenhum) | Sem contagem | Mais barato, padrão |

**[PROPOSTA]:** contagem **desligada por padrão**; só calculada quando `count=` for pedido. Em keyset, a contagem é feita **apenas na primeira página** (e opcionalmente reaproveitada), nunca a cada página. Usar `exact` só em tabelas pequenas ou filtros seletivos; `estimated` para telas com "cerca de N resultados". O objeto de página indica o **modo** usado para o total não ser tomado como exato por engano.

## 5. Objeto de página

**Page** (genérico no tipo do item; pseudo-estrutura):

- `items`: lista de itens (dicts ou modelos);
- `next_cursor`: cursor opaco, ou nulo se não houver mais;
- `has_more`: booleano. **[PROPOSTA]** calculado buscando `page_size + 1` linhas (sem precisar de contagem);
- `page_size`: tamanho efetivo pedido;
- `total`: opcional (nulo se contagem não pedida);
- `total_mode`: `exact` | `planned` | `estimated` | nulo;
- `offset`: presente só em paginação por offset;
- `prev_cursor`: **[PROPOSTA]** fora da v1.

Regra: `page_size` solicitado maior que o `max-rows` conhecido do servidor é **reduzido** ao teto efetivo (configurável: `server_max_rows`, padrão 1000) com log de aviso, em vez de devolver página silenciosamente truncada.

## 6. Iteração preguiçosa

- `iterate(table, *, filters, order_by, page_size, columns) -> Iterator[Item]`: gerador que busca página a página (keyset por padrão) e entrega item a item.
- Também `iterate_pages(...) -> Iterator[Page]` para quem processa por página/lote.
- Memória constante: no máximo uma página na memória; o consumidor decide quando parar (o gerador não busca a próxima página até ser necessário).
- Se o async for adotado (questão em aberto da visão geral), oferecer a versão assíncrona equivalente (`async for`); o contrato é o mesmo.
- Escolha de `columns`: encorajar projeção mínima em varreduras (menos tráfego).
- **Consistência:** a varredura **não é um snapshot**. Linhas inseridas/removidas durante a iteração podem ou não aparecer; keyset garante ao menos que não repete nem pula linhas já passadas pela ordenação. Documentar.
- Falha no meio: o gerador lança erro de domínio contendo o **último cursor bom**, permitindo retomar (`start_after=cursor`).
- Composição com lote: `iterate_pages` alimenta `update_many`/`delete_many` em pipelines. Cuidado ao **deletar enquanto itera com offset** (pula linhas); com keyset não há esse problema.

## 7. Limites do servidor e como a integração os respeita

1. `server_max_rows` configurável (padrão 1000) usado para limitar `page_size` e o teto de `batch_size` com `returning=representation`.
2. Detecção de truncamento: se uma resposta vier com exatamente `server_max_rows` itens e a consulta pedia mais, a integração trata como "possivelmente truncada" e continua paginando, nunca devolve como completa.
3. Consultas sem `limit` explícito (ex.: `get_all`) **não existem** na API pública: ou `list` paginado ou `iterate`. **[PROPOSTA]**
4. Timeouts do servidor/banco (`statement_timeout`) tornam páginas profundas por offset e contagens `exact` os candidatos naturais a falhar: mais um motivo para keyset.
5. Se o usuário alterar `max-rows` no projeto, basta atualizar `server_max_rows` na configuração (variável de ambiente; **[PROPOSTA]** adicionar ao guia de variáveis em [01-variaveis-de-ambiente.md](01-variaveis-de-ambiente.md) depois de decidido).
6. Rate limits e cotas do plano: ver questão em aberto 6.

## 8. Timeouts, retry e logs

### 8.1 Timeouts e retry

- Timeout **por requisição** (chunk ou página), configurável; **não** existe timeout global do lote (um lote grande é longo por natureza), mas **[PROPOSTA]** `deadline` opcional.
- Retry com backoff exponencial e jitter apenas para erros **transitórios** (rede, 408, 429, 5xx). Respeitar cabeçalho de espera quando o servidor informar.
- **Idempotência decide se o retry é seguro:** upsert, delete por id e update por id são idempotentes. **Insert puro não é**: um timeout após o servidor ter gravado pode duplicar. **[PROPOSTA]** insert em lote com retry automático só se a tabela tiver chave natural/única definida ou o chamador passar `retry_non_idempotent=True`; caso contrário, falha do chunk vira `failed` com marca "estado incerto".
- Retry atua **por chunk**, nunca refaz o lote inteiro.
- Número máximo de tentativas e backoff configuráveis.

### 8.2 Logs (seguindo a seção 3.2 da visão geral)

- **Início do lote** (INFO): operação, tabela, total de itens, `batch_size`, nº de chunks, modo `on_error`.
- **Progresso** (INFO, amostrado): não logar cada chunk. **[PROPOSTA]** emitir a cada **10%** de avanço **ou** a cada **N segundos** (o que vier primeiro), com: chunks feitos/total, itens ok/falhos, taxa (itens/s), tempo decorrido, ETA estimado.
- **Cada chunk** em DEBUG: índice, tamanho, duração, tentativas.
- **Retry** (WARNING): chunk, tentativa, motivo resumido, espera.
- **Falha de chunk** (ERROR): índice, intervalo de itens afetados, erro de domínio. Nunca o conteúdo dos registros; no máximo identificadores e nomes de colunas.
- **Fim do lote** (INFO, ou WARNING se houve falhas): resumo do BatchResult.
- Páginas em iteração: DEBUG por página; INFO só no início/fim e a cada N páginas.
- Aviso (WARNING) quando offset ultrapassa limiar, `page_size` é reduzido ao teto do servidor ou contagem `exact` é pedida em tabela marcada como grande.
- Cores e níveis seguem o padrão definido para o logger injetado; **nenhum segredo** em logs.

## 9. Paginação no Storage (frente de arquivos)

- A listagem do Storage é por **pasta/prefixo** dentro do bucket, com `limit` (padrão 100 na doc), `offset`, `sortBy` e `search`.
- **[PROPOSTA]** Contrato espelha o de tabelas: `list_objects(bucket, prefix, *, page_size, cursor, order_by) -> Page` com o mesmo objeto de página e `iterate_objects(...)`.
- Se a `listV2` (cursor) estiver disponível e estável, usá-la como mecanismo interno de cursor; se não, **cursor sintético** baseado em offset+ordenação (documentado como menos robusto sob escrita concorrente). **[A CONFIRMAR]** na doc oficial e no SDK Python escolhido.
- Ordenação: padrão por nome ascendente (determinística).
- Total: normalmente **não disponível** de forma barata; `total` fica nulo e `total_mode` nulo. Nada de contagem total por padrão.
- A listagem é **não recursiva** (por prefixo). Varredura recursiva é `iterate_objects(recursive=True)`, que desce pastas (entradas sem metadados de arquivo) com fila/pilha interna e memória limitada.
- Exclusão em lote de arquivos: `delete_objects(bucket, paths, *, batch_size)` em chunks, com o mesmo BatchResult. **[PROPOSTA]** `batch_size` padrão 100 (limite oficial **a confirmar**). Upload em lote: sequencial, um arquivo por vez, mesmo relatório por item (o tamanho dos arquivos torna o chunking por quantidade pouco relevante).

## 10. Contratos (pseudo-assinaturas, agnósticos ao SDK)

```
# Tabelas — em lote
insert_many(table, records, *, batch_size=None, on_error="stop", returning="minimal", atomic=False, dry_run=False) -> BatchResult
upsert_many(table, records, *, on_conflict, ignore_duplicates=False, batch_size=None, on_error="stop", returning="minimal") -> BatchResult
update_many(table, changes[(key, values)], *, key_column, batch_size=None, on_error="stop") -> BatchResult
update_where(table, values, filters, *, allow_unfiltered=False) -> UpdateResult
delete_many(table, keys, *, key_column, batch_size=None, on_error="stop") -> BatchResult
delete_where(table, filters, *, allow_unfiltered=False) -> DeleteResult

# Tabelas — leitura
list(table, *, filters, order_by, page_size, cursor=None, pagination="keyset", count=None, columns=None) -> Page
iterate(table, *, filters, order_by, page_size, columns=None, start_after=None) -> Iterator[Item]
iterate_pages(table, *, ...mesmos...) -> Iterator[Page]

# Storage
list_objects(bucket, prefix, *, page_size, cursor=None, order_by="name") -> Page
iterate_objects(bucket, prefix, *, page_size, recursive=False) -> Iterator[ObjectInfo]
delete_objects(bucket, paths, *, batch_size=None, on_error="stop") -> BatchResult

# Tipos
BatchResult { total_items, succeeded, failed, skipped, chunks_total, chunks_ok, chunks_failed, duration, aborted, items[ItemOutcome] }
ItemOutcome { index, status, record?, error? }
Page { items, next_cursor, has_more, page_size, total?, total_mode?, offset? }
BatchPolicy { batch_size, on_error, max_retries, backoff, deadline?, isolate_failures }
```

Todos os métodos são declarados nos contratos (interfaces) da classe de tabelas/arquivos e expostos pela fachada; o adapter traduz para `range`/filtros do SDK escolhido. Padrões vindos de configuração (`batch_size`, `server_max_rows`, política de retry) são injetados, não codificados.

## 11. Cenários de exemplo

1. **Importação de 12.000 registros (upsert, `on_error=continue`):** 24 chunks de 500; chunk 7 falha por timeout, retry com backoff resolve; chunk 15 falha por dado inválido, vai para o relatório; resultado: 11.500 ok, 500 falhos com índices originais. Log de progresso: ~10 linhas INFO no total.
2. **Varredura de tabela de 2 milhões de linhas:** `iterate` com keyset, `page_size=1000`, projeção de 3 colunas; memória constante; queda de rede na página 840 gera erro com o último cursor; a rotina retoma de `start_after`.
3. **Tela com "página N":** `list(pagination="offset", count="estimated")` devolve `total` aproximado com `total_mode="estimated"`.
4. **Pedido de `page_size=5000` com `max-rows` 1000:** reduzido a 1000 com WARNING; `has_more=true`.
5. **`delete_where` sem filtro:** recusado com erro de validação.
6. **Listagem de 3.000 imagens num bucket:** `iterate_objects(prefix="uploads/")`, páginas de 100, sem total.
7. **Upsert com ids repetidos no mesmo chunk:** deduplicado (último vence), relatório marca o descartado como `skipped` com motivo.

## 12. Critérios de aceite

- Lotes são divididos em chunks do tamanho configurado; tamanho acima do teto é rejeitado com erro claro.
- `stop` interrompe no primeiro chunk falho; `continue` processa todos; ambos devolvem BatchResult com status por item e posição original.
- `atomic=True` falha antes de enviar qualquer coisa se o lote não couber em um chunk.
- Retry ocorre só em erros transitórios e só em operações idempotentes (ou com opt-in); nunca refaz chunks já bem-sucedidos.
- `update_where`/`delete_where` sem filtro são recusados.
- Nenhuma listagem devolve resultado truncado em silêncio pelo `max-rows` do servidor.
- Paginação keyset: percorrer uma tabela de teste com inserções concorrentes não repete nem omite linhas já "passadas"; ordenação sempre determinística (PK como desempate).
- Contagem só é feita quando pedida; `total_mode` sempre informado junto do total.
- `iterate` mantém no máximo uma página em memória e não busca a seguinte antes do consumo.
- Falha em iteração informa o último cursor bom e permite retomar.
- Logs: sem uma linha por item; progresso amostrado; níveis/cores conforme padrão; nenhum segredo ou conteúdo de registro.
- Testável com um fake do contrato (sem rede), incluindo cenários de falha de chunk, timeout, truncamento por `max-rows` e cursor inválido.
- A listagem do Storage usa o mesmo objeto de página e funciona sem total.

## 13. Questões em aberto

1. **Async ou sync?** Define se `iterate` é gerador comum, assíncrono ou ambos. *Recomendação:* decidir junto à questão 2 da visão geral; manter contrato idêntico nos dois estilos.
2. **Valor real de `max-rows` no projeto** (padrão 1000, ajustável). *Recomendação:* consultar nas configurações da API (somente leitura) e registrar em `server_max_rows`.
3. **Tabelas candidatas ao primeiro uso têm PK única e coluna de ordenação NOT NULL?** Define se keyset serve na v1. *Recomendação:* sim, keyset por padrão; offset como fallback.
4. **Insert em lote precisa de retry seguro?** *Recomendação:* preferir upsert com chave natural onde possível; insert puro sem retry automático.
5. **Há necessidade de atomicidade entre chunks?** Exigiria RPC/função no banco (DDL, fora do escopo atual). *Recomendação:* não na v1; documentar a limitação.
6. **Plano/cotas e rate limits do projeto** (requisições por segundo, tamanho de payload). *Recomendação:* levantar na plataforma e ajustar `batch_size` e concorrência.
7. **Concorrência entre chunks** na v1? *Recomendação:* não; sequencial primeiro.
8. **Itens a confirmar na doc:** sintaxe exata de `range`/`count` no SDK Python, status 206 e cabeçalhos de contagem, `listV2` do Storage e limites de remoção em lote do Storage. *Recomendação:* confirmar na etapa de arquitetura antes de fechar os contratos.

## 14. Referências

Consultadas (as páginas do PostgREST responderam 429/redirecionamento e não puderam ser lidas; os pontos dependentes delas estão marcados "a confirmar"):

- Supabase, referência JS `select` (limite padrão de 1.000 linhas, `range`): <https://supabase.com/docs/reference/python/select>
- Supabase, referência Python `upsert` (`on_conflict`, `ignore_duplicates`, `returning`, `default_to_null`): <https://supabase.com/docs/reference/python/upsert>
- Supabase, Storage `list` (limit padrão 100, offset, sortBy, search): <https://supabase.com/docs/reference/javascript/storage-from-list>
- PostgREST, paginação e contagem (não lido; a verificar): <https://docs.postgrest.org/en/stable/references/api/pagination_count.html>
- Páginas tentadas e inexistentes/sem conteúdo útil: `https://supabase.com/docs/guides/api/using-pagination` (404), `https://supabase.com/docs/guides/database/pagination` (sem conteúdo sobre paginação).
