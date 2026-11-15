# Especificação: integração Supabase (backend)

> Status: **rascunho para aprovação**. Esta spec descreve **o quê** e **por quê**. O **como** está em [plan.md](plan.md); as tarefas em [tasks.md](tasks.md); as decisões em [decisions.md](decisions.md); os princípios em [constitution.md](constitution.md); o detalhamento técnico em [research/](research/).

## 1. Contexto e motivação

O projeto já tem uma integração com o Supabase que funciona (tabelas e arquivos), mas com falhas e margem de melhoria. Decidiu-se **não evoluir nem reaproveitar** essa implementação: será construída uma integração nova, do zero, isolada em `supabase/` (princípio P1). A integração antiga continua intacta; a substituição, se houver, é uma fase futura.

## 2. Objetivo

Dar ao **backend** uma integração completa, flexível e de fácil manutenção com o Supabase, em duas frentes, por meio de **uma única classe de entrada**.

| Frente | Capacidade |
|---|---|
| **A. Tabelas** | CRUD completo: criar/inserir, buscar, atualizar/editar, deletar. |
| **B. Arquivos** | Salvar, recuperar e deletar arquivos em buckets. Qualquer tipo: imagem, áudio, vídeo, documento. |
| **C. Integração** | Uma classe que combina A e B e expõe todo o fluxo Supabase em um ponto só. |

Consumidor: o backend (não o usuário final). Referência oficial: <https://supabase.com/docs/guides/getting-started/quickstarts/flask>.

## 3. Histórias de usuário (do ponto de vista do backend)

Prioridade: P0 = essencial na v1, P1 = importante na v1, P2 = desejável / pode ficar para depois.

| ID | História | Prio |
|---|---|---|
| US-1 | Como backend, quero **inserir, buscar, atualizar e deletar** registros de uma tabela sem conhecer o SDK do Supabase. | P0 |
| US-2 | Como backend, quero **salvar, recuperar e deletar arquivos** de qualquer tipo em um bucket, inclusive grandes. | P0 |
| US-3 | Como backend, quero **uma única classe** que me dê tudo isso, já montada e configurada. | P0 |
| US-4 | Como desenvolvedor, quero **logs claros, coloridos e com nível configurável** para depurar. | P0 |
| US-5 | Como desenvolvedor, quero que **configuração inválida falhe ao iniciar**, dizendo o que falta. | P0 |
| US-6 | Como backend, quero **erros do domínio** (não do SDK) e **retry** automático só onde é seguro. | P0 |
| US-7 | Como backend, quero **listar com filtros, ordenação e paginação** e varrer tabelas grandes sem estourar memória. | P1 |
| US-8 | Como backend, quero **operações em lote** (inserir/atualizar/upsert/deletar) com resultado por item. | P1 |
| US-9 | Como backend, quero **operações combinadas** (arquivo + registro) com resultado `completa`/`parcial`/`falhou` e compensação de melhor esforço. | P1 |
| US-10 | Como desenvolvedor, quero **testar tudo sem rede** (fakes) e, separadamente, contra um projeto de teste. | P0 |
| US-11 | Como backend, quero **URL assinada** com expiração controlada para arquivos privados. | P1 |
| US-12 | Como desenvolvedor, quero um **exemplo de uso e README** da integração. | P2 (após a implementação) |

## 4. Requisitos funcionais

### 4.1 Frente A: tabelas (detalhe: [research/06](research/06-modelagem-de-dados.md), [research/09](research/09-lote-e-paginacao.md))
- **FR-A1** Inserir um registro e inserir em lote.
- **FR-A2** Buscar por id, por filtros (árvore de condições com operadores v1), com seleção de colunas, ordenação e paginação; listar.
- **FR-A3** Atualizar por id e por filtro.
- **FR-A4** Deletar por id e por filtro. Delete de inexistente é **sucesso idempotente** (informa se removeu algo).
- **FR-A5** Upsert por chave de conflito.
- **FR-A6** `get_by_id` inexistente lança `RecordNotFoundError`; busca por filtro sem linhas devolve lista vazia; atualizar inexistente lança `RecordNotFoundError`.
- **FR-A7** Update/delete **sem filtro são recusados**.
- **FR-A8** Registros como `dict` ou modelo tipado (descritor de tabela, abordagem híbrida). Nova tabela entra **sem alterar código existente**.
- **FR-A9** Paginação (offset na v1; cursor/keyset opcional) e iteração preguiçosa para varrer tabelas grandes; nunca truncar resultado em silêncio ao bater no limite do servidor.
- **FR-A10** Lote com divisão em chunks, modos `stop`/`continue` e relatório por item.

### 4.2 Frente B: arquivos (detalhe: [research/07](research/07-arquivos-grandes-e-storage.md))
- **FR-B1** Upload de arquivo a partir de caminho, bytes ou stream; modo padrão para pequenos e **resumable** para grandes, sem carregar tudo em memória.
- **FR-B2** Download (bytes ou para arquivo) e **URL pública** ou **assinada** (com TTL controlado).
- **FR-B3** Exclusão (um, lote, por prefixo).
- **FR-B4** Listagem paginada de objetos de um bucket/pasta.
- **FR-B5** Validação **antes** do upload: tamanho, extensão, MIME e conteúdo (magic bytes); recusa se divergirem.
- **FR-B6** Caminho gerado pela integração (pasta por data + UUID, nome original saneado como metadado) com estratégias de nomeação injetáveis.
- **FR-B7** Colisão: `reject` por padrão; `version` para substituição lógica; `overwrite` só explícito.
- **FR-B8** Qualquer tipo de mídia suportado; allowlist de buckets.

### 4.3 Classe integradora (detalhe: [research/08](research/08-consistencia-entre-frentes.md))
- **FR-C1** Expor `tables` e `storage` e as operações combinadas por um único objeto, montado por uma Factory.
- **FR-C2** Operações combinadas com ordem fixa (grava: arquivo → registro; apaga: registro → arquivo), compensação de melhor esforço, resultado `completa`/`parcial`/`falhou` e log com `orfao_possivel=true` quando sobrar órfão.
- **FR-C3** A fachada não captura nem traduz erros das duas classes; propaga o mesmo objeto de exceção.

### 4.4 Transversais
- **FR-T1 Configuração** (detalhe: [research/03](research/03-configuracao-centralizada.md)): objeto imutável, validado na criação, em fatias, sem variáveis globais.
- **FR-T2 Erros e resiliência** (detalhe: [research/02](research/02-tratamento-de-erros-e-resiliencia.md)): hierarquia de exceções, timeouts explícitos, retry com backoff e jitter em um único lugar.
- **FR-T3 Logs:** níveis, cores, campos estruturados, sanitizador sem segredos, logger injetado.
- **FR-T4 Segurança** (detalhe: [research/05](research/05-seguranca-de-dados.md)): allowlists de tabelas, colunas e buckets; sanitização de caminhos; chave secreta mascarada; URLs assinadas com teto de expiração.

## 5. Requisitos não funcionais
- **NFR-1** Independência (P1) e isolamento do SDK (P4), verificados por teste de arquitetura.
- **NFR-2** Testável offline; cobertura mínima inicial de 90% de linhas e 80% de ramos nos testes offline ([research/04](research/04-estrategia-de-testes.md)).
- **NFR-3** Python 3.12, dependências via `uv`; nenhuma dependência nova além do necessário (ver [decisions.md](decisions.md)).
- **NFR-4** Contratos estáveis: mudar o SDK ou o provedor só afeta `adapters/`.
- **NFR-5** Arquivos grandes nunca bloqueiam o event loop (uso via thread) e respeitam um teto de memória.

## 6. Fora de escopo (v1)
- Reaproveitar, migrar ou refatorar a integração Supabase existente.
- Integrar o código novo ao restante do projeto (fase futura, com spec própria).
- Alterações de schema (DDL/migrations/RPC) feitas pela integração.
- Supabase Auth (usuários finais), Realtime, Edge Functions.
- Interface de usuário.
- Atomicidade entre chunks de lote e transação entre Postgres e Storage.
- Circuit breaker, estado pendente/confirmado, rotina de limpeza de órfãos, trigger no banco, varredura antivírus, upload direto do cliente final por URL assinada (todos como evolução; ver [research/08](research/08-consistencia-entre-frentes.md) seção 10).
- Relações embutidas (joins) e geração de tipos a partir do schema.

## 7. Critérios de sucesso da v1
1. Os requisitos P0 e P1 das histórias estão implementados e cobertos por testes offline.
2. `supabase/` não importa nada do código existente do projeto e o `import supabase` do SDK continua funcionando (sem sombreamento).
3. Suíte de integração passa contra um projeto Supabase de teste (quando houver credenciais), incluindo upload grande.
4. O teste de "segredo plantado" prova que nenhum segredo aparece em logs, exceções ou `repr`.
5. Subir com configuração incompleta falha na Factory, listando só os nomes das variáveis.
6. A checklist de segurança de [research/05](research/05-seguranca-de-dados.md) (seção 11) foi revisada e aprovada.
