# Modelagem de dados da Frente A (Tabelas)

> **Material de pesquisa (refinamento técnico).** A visão geral citada aqui como "00" / "visão geral" agora vive em [../spec.md](../spec.md). As "Questões em aberto" deste arquivo estão **consolidadas e resolvidas em [../decisions.md](../decisions.md)**, que prevalece em caso de divergência. Tarefas de implementação: [../tasks.md](../tasks.md).

> Status: **rascunho de planejamento** (nenhum código escrito). Itens marcados como **[PROPOSTA]** são sugestões a validar; decisões pendentes estão em "Questões em aberto". Complementa [spec.md](../spec.md) e [01-variaveis-de-ambiente.md](01-variaveis-de-ambiente.md).

## 1. Contexto e escopo

A classe de tabelas (`SupabaseTables`, nome provisório) faz o CRUD sobre o Postgres do Supabase via PostgREST. Este documento define **como os registros são representados, como as consultas são expressas e como os tipos do Postgres são tratados**, de modo que:

- o contrato da classe seja **genérico** e não conheça nenhuma tabela específica;
- o backend nunca veja detalhes do SDK (`supabase-py`/PostgREST), que ficam no **adapter**;
- adicionar uma tabela nova **não exija editar código existente** (Open/Closed);
- nada seja importado da integração Supabase atual do projeto.

Fora deste documento: contratos de arquivos (frente B), logs, configuração/credenciais e hierarquia de erros (docs próprios). Aqui só se citam erros quando afetam a modelagem.

## 2. Como representar registros

### 2.1 Opções avaliadas

| Opção | Prós | Contras |
|---|---|---|
| **A. Dicionários genéricos** (`dict[str, Any]`) | Zero cerimônia; nova tabela sem nenhuma classe; espelha o JSON do PostgREST | Sem validação nem autocompletar; erros de nome de coluna só em runtime; tipos do Postgres chegam como strings (uuid, timestamptz); contrato fraco entre camadas |
| **B. Um modelo Pydantic por tabela, com métodos de CRUD por tabela** | Tipagem forte | Explosão de classes de acesso; duplica lógica; acopla a classe de tabelas a tabelas específicas; viola Open/Closed |
| **C. Híbrida: repositório genérico tipado + modelo Pydantic opcional por tabela** | Contrato único e genérico; tipagem e validação quando o modelo existe; dict continua possível para casos ad hoc; nova tabela = novo modelo + registro, sem tocar no núcleo | Um pouco mais de conceitos (repositório, modelo, registro de tabela); exige disciplina para manter modelo alinhado ao schema |

### 2.2 Recomendação

**Opção C (híbrida)**. O núcleo trabalha com um repositório genérico parametrizado por um tipo de entidade; cada tabela é descrita por um **descritor de tabela** (nome, schema, chave primária, modelo Pydantic opcional). Sem modelo, a entidade é `dict`. Isso responde à questão em aberto 4 de `spec.md`.

Regra prática **[PROPOSTA]**: modelos tipados para tabelas de uso recorrente e contrato estável; `dict` para exploração, scripts e tabelas ainda não estabilizadas.

## 3. Contrato genérico da classe de tabelas

### 3.1 Tipagem com generics

O contrato é parametrizado por um tipo de entidade `E` (modelo Pydantic ou `dict`) e por um tipo de id `K` (`UUID`, `int`, `str`). Em pseudo-assinaturas:

```
TableRepository[E, K]            # contrato (Protocol/ABC), sem conhecer tabela alguma
  get(id: K, *, select=None) -> E | None
  require(id: K, *, select=None) -> E                 # lança NotFound
  find(query: Query = Query()) -> list[E]
  page(query: Query, page: PageRequest) -> Page[E]
  count(filters: Filter | None = None) -> int
  insert(data: E | dict) -> E
  insert_many(data: Sequence[E | dict]) -> list[E]
  update(id: K, patch: dict | E) -> E                 # lança NotFound se não casar
  update_where(filters: Filter, patch) -> list[E]
  upsert(data: E | dict, *, on_conflict: Sequence[str]) -> E
  delete(id: K) -> bool
  delete_where(filters: Filter) -> int                # exige filtro não vazio
```

A classe `SupabaseTables` (primeira das três classes) **não é um repositório por tabela**. Ela é a porta de entrada que entrega repositórios:

```
SupabaseTables
  table(descriptor: TableDescriptor[E, K]) -> TableRepository[E, K]
  table(name: str) -> TableRepository[dict, Any]      # atalho schemaless, entidade = dict
```

`TableRepository` é implementado por **um único adapter genérico** (sobre PostgREST). O que varia por tabela é só o descritor. Assim a classe de tabelas fica agnóstica: ela depende de `TableRepository` (abstração) e de `TableDescriptor` (dados), nunca de uma tabela concreta.

### 3.2 Descritor de tabela

Objeto de valor imutável com:

- `name` e `schema` (padrão `public`);
- `primary_key`: nome(s) da coluna(s) (padrão `id`);
- `model`: classe Pydantic opcional (ausente significa `dict`);
- `select_default`: colunas padrão (padrão: todas);
- `server_managed_columns`: colunas geradas pelo banco, ignoradas no insert/update (ex.: `id`, `created_at`, `updated_at`);
- `soft_delete_column` **[PROPOSTA]**, opcional: se presente, `delete` vira marcação, não remoção física (ver questões em aberto).

## 4. Consultas agnósticas ao SDK

### 4.1 Query Object

O backend monta consultas com objetos de valor próprios, sem ver `.eq()`, `.in_()` etc. do SDK. Elementos:

- **Filter** (árvore): condição simples `(coluna, operador, valor)` ou composição `and_`/`or_`/`not_` de filtros. Construído por funções utilitárias legíveis, ex.: `eq("status", "ativo")`, `gte("criado_em", dt)`, `and_(...)`.
- **Sort**: lista de `(coluna, direção, nulos_primeiro|nulos_por_ultimo)`.
- **Select**: lista de colunas; suporte a **colunas de relação embutida** (embedded resources do PostgREST) é **[PROPOSTA]** e opcional na v1.
- **Query**: agrega `filters`, `sort`, `select`, `limit`, `offset`.
- **PageRequest**: `page` e `size` (ou `limit`/`offset`), com teto máximo configurável.

A abordagem é a de **Query Object**, com filtros no estilo **Specification** (composáveis, testáveis sem rede).

### 4.2 Conjunto de operadores (v1)

Enumeração própria (`Op`), mapeada 1:1 para operadores PostgREST:

| Op próprio | PostgREST | Observação |
|---|---|---|
| `EQ`, `NEQ` | `eq`, `neq` | |
| `GT`, `GTE`, `LT`, `LTE` | `gt`, `gte`, `lt`, `lte` | |
| `IN`, `NOT_IN` | `in`, `not.in` | lista vazia em `IN` retorna vazio sem ir à rede **[PROPOSTA]** |
| `LIKE`, `ILIKE` | `like`, `ilike` | o chamador escapa `%`/`_` por helper próprio |
| `IS_NULL`, `NOT_NULL` | `is.null`, `not.is.null` | |
| `CONTAINS`, `CONTAINED_BY`, `OVERLAPS` | `cs`, `cd`, `ov` | arrays e jsonb |
| `JSON_PATH_EQ` **[PROPOSTA]** | `col->chave` / `col->>chave` | acesso a campos de jsonb |
| `TEXT_SEARCH` **[PROPOSTA]** | `fts`/`plfts`/`wfts` | adiar para v2 se não houver caso real |

Operadores fora da lista exigem **extensão** (novo membro na tabela de tradução), nunca mudança nos chamadores.

### 4.3 Tradução para PostgREST (papel do adapter)

O adapter possui um **tradutor de Query** que percorre a árvore de filtros e aplica no builder do SDK:

- condição simples vira chamada do operador correspondente;
- `and_` é o comportamento padrão (filtros encadeados); `or_` e `not_` viram a sintaxe de grupo do PostgREST (`or=(...)`, `not.`), com **escape** de valores que contenham vírgula, parênteses ou pontos;
- `Sort` vira `order(coluna, desc, nullsfirst)`;
- `Select` vira a string de `select`; sem seleção, usa `select_default` do descritor;
- paginação vira `range(inicio, fim)` (PostgREST usa intervalo inclusivo); `count` usa o cabeçalho de contagem (`exact`, `planned` ou `estimated`, configurável; padrão `exact` apenas quando `page()` for chamado **[PROPOSTA]**).

Tradução é função pura do `Query` para chamadas do builder; deve ser testada **sem rede**, comparando a requisição montada.

### 4.4 Segurança de consulta

- Nomes de coluna e tabela vindos de entrada externa são validados contra o descritor (lista permitida) antes de entrar na consulta, evitando injeção via nome de coluna.
- `update_where` e `delete_where` **recusam filtro vazio** (evita apagar/atualizar a tabela inteira por engano). Para operar em tudo, exige-se flag explícita (ex.: `allow_all=True`).
- Limite padrão e teto de `limit`, pois o PostgREST aplica um máximo de linhas por requisição configurado no projeto.

## 5. Formato de retorno

| Operação | Retorno |
|---|---|
| `get` | `E` ou `None`; `require` lança `NotFound` |
| `find` | `list[E]` (pode ser vazia; nunca `None`) |
| `page` | `Page[E]`: `items`, `total` (se contado), `page`, `size`, `has_next` |
| `insert`/`update`/`upsert` | entidade resultante **com valores do banco** (ids, defaults, timestamps), via retorno de representação |
| `insert_many` | lista na mesma ordem enviada |
| `delete` | `bool` (existia ou não); `delete_where` retorna a contagem afetada |
| `count` | `int` |

`Page[E]` é objeto de valor genérico. Cursor/keyset em vez de offset fica como **[PROPOSTA]** para tabelas grandes (offset degrada com volume).

Observação: por padrão o PostgREST pode não devolver o registro após escrita; o adapter deve solicitar explicitamente a representação de retorno para cumprir o contrato acima.

## 6. Tipos do Postgres

O PostgREST trafega **JSON**. O adapter e o modelo Pydantic fazem a conversão nas duas direções. Tabela de tratamento:

| Tipo Postgres | Representação em Python (modelo tipado) | Em `dict` | Cuidados |
|---|---|---|---|
| `uuid` | `uuid.UUID` | `str` | Serializar como string canônica; validar formato na entrada |
| `text`/`varchar` | `str` | `str` | |
| `int4`/`int8` | `int` | `int` | `int8` acima de 2^53 pode perder precisão em clientes JS; no backend Python não há perda |
| `numeric`/`decimal` | `decimal.Decimal` | `int`/`float` conforme JSON | PostgREST pode devolver número JSON; parsear para `Decimal` sem passar por `float` quando precisão importar (dinheiro). **[PROPOSTA]** modelo declara `Decimal` e o adapter parseia JSON com `parse_float=Decimal` |
| `float4/8` | `float` | `float` | |
| `boolean` | `bool` | `bool` | |
| `timestamptz` | `datetime` **com tzinfo** (UTC) | `str` ISO 8601 | Entrada: exigir datetime ciente de fuso; recusar *naive* ou assumir UTC por regra explícita **[PROPOSTA: recusar]**. Saída: converter para UTC |
| `timestamp` (sem fuso) | `datetime` naive | `str` | Evitar em novas tabelas; documentar se existir |
| `date` / `time` | `date` / `time` | `str` | |
| `jsonb`/`json` | `dict`, `list` ou sub-modelo Pydantic | `dict`/`list` | Não confundir `None` Python com JSON `null` vs coluna SQL `NULL`; definir regra (ver 6.1) |
| arrays (`text[]`, `int[]`, `uuid[]`) | `list[T]` | `list` | Em filtros, usar `CONTAINS`/`OVERLAPS`; valores de array em filtros PostgREST usam sintaxe `{a,b}` que o adapter gera |
| `bytea` | `bytes` | `str` (hex/base64 conforme resposta) | Evitar; para binários usar a frente de arquivos |
| enums Postgres | `enum.Enum`/`Literal` | `str` | Valor desconhecido na leitura deve falhar de forma clara (modelo) |

### 6.1 Nulos e "campo ausente"

Distinguir **omitido** (não enviar, mantém o valor no `update`) de **`None`** (enviar `null`, grava NULL). Para isso o serializador de escrita usa "excluir não definidos" (`exclude_unset`) em updates parciais. Regra **[PROPOSTA]**: update parcial só envia campos explicitamente definidos.

## 7. Chaves primárias e id

- Padrão: coluna `id`, tipo `uuid` (ou `bigint` identity), **gerada pelo banco** (`default gen_random_uuid()` ou identity). A integração **não gera ids** por padrão; recebe do retorno do insert.
- O descritor declara `primary_key`; chave **composta** é suportada como tupla/mapeamento (`K` = tupla), com `get/update/delete` filtrando por todas as colunas.
- `upsert` exige `on_conflict` explícito (colunas com restrição única); não adivinhar.
- Se o chamador fornecer o id no insert (migração de dados, idempotência), é permitido quando a coluna não está em `server_managed_columns`. Idempotência por id gerado no cliente é **[PROPOSTA]** para fluxos que repetem inserts.

## 8. Serialização e desserialização

Fluxo de escrita: `E | dict` -> **validação** -> **serialização para JSON-compatível** -> remoção de `server_managed_columns` -> envio. Fluxo de leitura: JSON -> **mapeamento** para `E` (validação Pydantic) -> retorno.

Responsabilidades:

- Um **codec** por entidade (derivado do modelo Pydantic, ou identidade para `dict`) com `to_wire(entity) -> dict JSON-safe` e `from_wire(dict) -> E`. Fica no adapter/camada de mapeamento, não nas classes de domínio.
- `to_wire` converte `UUID`, `datetime`, `Decimal`, `Enum`, `set` em tipos JSON; nunca depende de `default=str` genérico (esconde erros).
- Mapeamento de nomes: por padrão, **nome do campo = nome da coluna** (snake_case). Alias só quando necessário (`Field(alias=...)`), declarado no modelo.
- Colunas extras vindas do banco: modelo configurável para **ignorar** extras na leitura (tolera evolução do schema) e **proibir** extras na escrita (pega erros de digitação). **[PROPOSTA]**
- Falha de desserialização vira erro de domínio (`MappingError`/`SchemaMismatch`) citando tabela e campo, sem registrar o conteúdo do registro nos logs (regra de logs de `spec.md`).

## 9. Validação de dados na entrada

Camadas, da mais barata para a mais cara:

1. **Modelo Pydantic** (quando existe): tipos, obrigatoriedade, formatos, tamanhos, regras de negócio simples. Falha antes de qualquer rede.
2. **Descritor**: recusa colunas desconhecidas, recusa escrita em colunas gerenciadas pelo servidor, exige filtro em operações em massa.
3. **Banco** (constraints, FKs, unique, RLS): fonte final da verdade. O adapter **traduz erros do PostgREST/Postgres** (ex.: violação de unicidade, FK, not null, check, permissão) em erros de domínio distintos (`Conflict`, `ReferenceViolation`, `ConstraintViolation`, `PermissionDenied`, `NotFound`), preservando o código original como atributo, sem vazar exceções do SDK.

Para `dict` sem modelo, só valem as camadas 2 e 3. Isso é o custo consciente da flexibilidade.

Sobre credenciais: com a chave secreta (service role) o RLS é ignorado; a validação das camadas 1 e 2 é, portanto, a principal barreira no backend. Detalhe de credenciais fica em doc próprio.

## 10. Adicionar uma tabela sem alterar código existente (Open/Closed)

Fluxo previsto **[PROPOSTA]**:

1. Criar um novo módulo (ex.: `models/<tabela>.py`) com o **modelo Pydantic** e o **descritor** da tabela.
2. **Registrar** o descritor num **registro de tabelas** (`TableRegistry`), por chamada explícita no módulo de composição ou por descoberta automática de módulos na pasta `models/` (padrão parecido com a descoberta de rotas que o projeto já usa, mas sem importar nada dele). Recomendação: registro **explícito** (mais rastreável) com descoberta opcional.
3. Usar: `tables.table(Descritor)` ou `tables.get("nome")`.

Nenhum arquivo do núcleo (contrato, adapter, tradutor de queries, classe integradora) é editado. Comportamentos específicos de uma tabela (ex.: coluna de soft delete, validação extra) entram por **dados no descritor** ou por **decoradores/estratégias** sobre o repositório, não por `if tabela == ...` no núcleo.

A tabela precisa existir no banco; **criar tabela/DDL está fora de escopo** (ver `spec.md`, seção 5).

## 11. Objetos de valor para metadados de arquivo (relação com a frente B)

A frente de arquivos (storage) e a de tabelas são independentes (uma não conhece a outra), mas é comum guardar numa tabela o **registro de um arquivo** (quem enviou, bucket, caminho, tipo, tamanho). Proposta para manter o desacoplamento:

- Definir **objetos de valor neutros** em módulo compartilhado e sem dependência de SDK, **[PROPOSTA]**:
  - `StorageRef`: `bucket`, `path` (identifica o objeto no storage; imutável, igualdade por valor).
  - `FileMetadata`: `ref: StorageRef`, `content_type`, `size_bytes`, `checksum` (opcional), `created_at` (UTC).
- A frente B **produz** `FileMetadata` ao salvar; a frente A **persiste** esse objeto como colunas (ou `jsonb`) em uma tabela de aplicação, mapeado por um modelo comum (ex.: tabela `arquivos` do domínio, a definir com o usuário).
- Nenhuma classe de A importa classes de B (e vice-versa); ambas importam só os objetos de valor. A **classe integradora** (fachada) pode oferecer um fluxo composto "salvar arquivo e registrar metadados", mas **sem lógica própria**: delega a B e depois a A. Consistência (arquivo salvo mas registro falhou, ou o contrário) é decisão em aberto (item 4 abaixo).
- O objeto guarda o **caminho**, não URL assinada (que expira); a URL é gerada sob demanda pela frente B.

## 12. Cenários (em prosa)

1. **Criar e ler com modelo tipado.** O backend monta um modelo `Documento` com título e tags (array) e chama `insert`. O banco gera `id` e `created_at`; a resposta volta como `Documento` completo, com `id` como `UUID` e `created_at` como `datetime` em UTC. Depois `get(id)` devolve o mesmo.
2. **Listagem paginada com filtro composto.** Pedir documentos `status = ativo` **e** (`tags` contém `ia` **ou** `criado_em` nos últimos 7 dias), ordenados por `criado_em` decrescente, página 2 de 20. O chamador monta `Filter` e `PageRequest`; o adapter traduz para filtros PostgREST e faixa de linhas; o retorno é `Page[Documento]` com `total` e `has_next`.
3. **Tabela ad hoc sem modelo.** Um script de manutenção usa `tables.table("logs_importacao")` e recebe `dict`. Sem validação de tipos; apenas as proteções do descritor genérico (filtro obrigatório em delete em massa).
4. **Update parcial.** Alterar apenas `status`. Só esse campo é enviado; `titulo` não é tocado. Um `None` explícito em `descricao` grava NULL; o campo omitido permanece.
5. **Conflito de unicidade.** Inserir registro com chave única já existente: o banco rejeita; o adapter devolve `Conflict` com o nome da restrição, e o backend decide entre abortar ou usar `upsert` com `on_conflict`.
6. **Dinheiro.** Coluna `numeric(12,2)`: o modelo declara `Decimal`; o adapter parseia o JSON sem `float`, evitando erro de arredondamento.
7. **Nova tabela `projetos`.** Alguém adiciona `models/projetos.py` (modelo + descritor) e registra. Nenhum arquivo do núcleo muda; testes unitários do tradutor e do codec seguem válidos.
8. **Arquivo com registro.** A frente B salva um PDF e devolve `FileMetadata`; o backend persiste esse objeto via frente A na tabela de arquivos do domínio; mais tarde, para baixar, usa `StorageRef` guardado, não uma URL antiga.

## 13. Critérios de aceite

- O contrato `TableRepository[E, K]` compila/tipa sem referência a tabela específica e sem importar o SDK do Supabase.
- Um fake em memória do contrato passa a mesma suíte de testes do adapter (substituição de Liskov).
- O tradutor de queries cobre todos os operadores da seção 4.2 com testes sem rede, incluindo `or_`/`not_` aninhados e valores com caracteres especiais.
- `update_where`/`delete_where` com filtro vazio falham por padrão.
- Round-trip de cada tipo da seção 6 (uuid, timestamptz com fuso, numeric sem perda, jsonb, array) validado contra um projeto de teste.
- Escrita recusa colunas gerenciadas pelo servidor; leitura tolera colunas extras.
- Erros do banco chegam como erros de domínio, sem exceções do SDK vazando.
- Adicionar uma tabela de exemplo exige apenas novos arquivos (verificável por diff).
- Nenhum log contém valores de registros ou segredos.
- Zero imports da integração Supabase existente.

## 14. Questões em aberto

1. **Modelos tipados desde a v1?** Recomendação: sim, abordagem híbrida (opção C), com `dict` como porta de saída. Depende de quais tabelas serão os primeiros casos reais.
2. **Tipo de id padrão** (uuid x bigint identity)? Recomendação: `uuid`, salvo tabelas já existentes com outro padrão.
3. **Soft delete**: usar por padrão em alguma tabela? Recomendação: não por padrão; opt-in no descritor.
4. **Consistência arquivo + registro** (frentes A e B): tolerar órfãos com rotina de limpeza, ou compensação (apagar o arquivo se o registro falhar)? Recomendação: compensação simples (apagar o arquivo) na fachada e documentar o risco residual.
5. **Timestamps sem fuso na entrada**: recusar ou assumir UTC? Recomendação: recusar.
6. **Estratégia de paginação**: offset basta ou algumas tabelas pedem cursor? Recomendação: offset na v1, cursor sob demanda.
7. **Schemas além de `public`** e relações embutidas (joins via select) na v1? Recomendação: schema configurável por descritor; relações embutidas só na v2.
8. **Síncrono ou assíncrono** (questão 2 de `spec.md`) afeta as assinaturas deste contrato (`async def` ou não). Recomendação: decidir antes de fechar contratos; os desenhos acima valem nos dois casos.
9. **Geração de tipos a partir do schema do banco** (para manter modelos alinhados): vale adotar? Recomendação: avaliar depois da v1; começar com modelos escritos à mão e teste de verificação contra o schema.

## 15. Referências

Documentação oficial do Supabase/PostgREST que fundamenta as decisões (conferir a versão atual na implementação; este rascunho não substitui a leitura delas):

- <https://supabase.com/docs/reference/python/introduction>
- <https://supabase.com/docs/reference/python/select>
- <https://supabase.com/docs/reference/python/insert>
- <https://supabase.com/docs/reference/python/upsert>
- <https://supabase.com/docs/reference/python/using-filters>
- <https://supabase.com/docs/reference/python/order>
- <https://supabase.com/docs/reference/python/range>
- <https://supabase.com/docs/guides/api/joins-and-nesting>
- <https://supabase.com/docs/guides/database/json>
- <https://supabase.com/docs/guides/database/arrays>
- <https://supabase.com/docs/guides/database/postgres/row-level-security>
- <https://postgrest.org/en/stable/references/api/tables_views.html>
- <https://supabase.com/docs/guides/getting-started/quickstarts/flask> (citada na visão geral)
