# Tarefas de implementação

Ordem de execução da [spec](spec.md), seguindo o [plano](plan.md). **Nenhuma tarefa de código começa antes de a Fase 0 estar concluída.**

**Convenções:** `[P]` = pode rodar em paralelo com outras da mesma fase. `Dep:` = pré-requisitos. `Ref:` = pesquisa de apoio. **Teste primeiro:** cada tarefa de código começa pelos testes descritos nos critérios. Marque `[x]` ao concluir.

---

## Fase 0: decisões, preparação e verificações

- [ ] **T-000** Confirmar as decisões D-01 a D-08 em [decisions.md](decisions.md) e trocar ❓ por ✅ (ou ajustar). *Critério:* nenhuma decisão ❓ restante.
- [ ] **T-001** Levantar credenciais e dados da plataforma seguindo [research/01](research/01-variaveis-de-ambiente.md) (Chrome primeiro; **somente leitura**; só nomes no relatório): Project URL, chave secreta, buckets (e visibilidade), tabelas candidatas, plano, limite global de upload, `max-rows`. Registrar em [decisions.md](decisions.md) (D-04, D-05). Dep: T-000. *Critério:* variáveis `SBX_*` acrescentadas ao `.env` sem tocar nas `SUPABASE_*` existentes; relatório sem valores.
- [ ] **T-002** Criar o esqueleto: `supabase/bai_supabase/` com subpacotes vazios do plano, `supabase/tests/`, `supabase/pytest.ini` (`pythonpath = .`). **Sem** `__init__.py` em `supabase/`. Dep: T-000.
- [ ] **T-003** Adicionar `pytest`, `pytest-socket`, `pytest-cov` (e `filetype`, cliente TUS se confirmados) ao `pyproject.toml` e rodar `uv sync`. Dep: T-000. *Critério:* `uv run pytest supabase/tests` executa e coleta zero testes sem erro.
- [ ] **T-004** Teste de sombreamento: `python -c "import supabase; print(supabase.__file__)"` a partir da raiz **e** de `supabase/` aponta para o SDK em `.venv`. Dep: T-002. *Critério:* passa; vira teste permanente em `tests/architecture/`.
- [ ] **T-005** Verificar no SDK instalado (versão do `uv.lock`): exceções reais de PostgREST e Storage, sintaxe de `range`/`count`, `upsert`, remoção em lote, `list`/`listV2`, opções de timeout do cliente HTTP, opção de TUS. Registrar achados em [decisions.md](decisions.md) §4. Dep: T-003. Ref: 02 §2, 07 §2, 09 §2.
- [ ] **T-006** Criar `supabase/.env.example` e `.env.test.example` (só nomes, conforme tabelas de [research/03](research/03-configuracao-centralizada.md) §5 com as decisões C-3, C-4, C-6). Dep: T-000.

## Fase 1: fundação (sem rede)

- [ ] **T-101** `[P]` **Erros:** hierarquia completa e atributos comuns, `__cause__` preservado. Dep: T-002. Ref: 02 §3. *Critério:* teste de cada classe e de `retryable` padrão (02 §6).
- [ ] **T-102** `[P]` **Sanitizador** (função pura) e **tipo `Secret`** com `repr` mascarado. Dep: T-002. Ref: 02 §10.3, 05 §3, §9. *Critério:* teste do "segredo plantado" em mensagem, `details`, URL e cabeçalhos; trunca valores de linha do Postgres.
- [ ] **T-103** **Logger:** contrato, implementação com níveis, cores (auto/on/off, `NO_COLOR`, não-TTY), formatos `pretty`/`json`, campos estruturados, truncamento. Dep: T-102. Ref: spec FR-T3, 03 §5.4. *Critério:* testes de nível, ANSI presente/ausente, JSON válido, nenhum segredo.
- [ ] **T-104** **Config:** `SupabaseSettings` em fatias, `SettingsSource` (Env, Dotenv, Dict), `SettingsLoader` com erro agregado só com nomes, regras por ambiente (allowlists obrigatórias em prod, `.env` só em dev, proteção `EXPECTED_PROJECT_REF`). Dep: T-102. Ref: 03. *Critério:* 03 §12 itens 1–10.
- [ ] **T-105** **Mapeador de erros** (função pura) a partir de "erro bruto normalizado": tabelas, storage e transporte. Dep: T-101, T-005. Ref: 02 §5. *Critério:* teste de tabela cobrindo todos os códigos de 02 §5.2–5.4 e o caso desconhecido → `UnexpectedError`.
- [ ] **T-106** **Resiliência:** políticas de timeout e retry (backoff exponencial, jitter, `retry_budget`, `Retry-After`), executor com idempotência declarada, relógio/aleatório injetáveis, ponto de extensão para breaker. Dep: T-101, T-103. Ref: 02 §7–§9. *Critério:* retry só em idempotente + `retryable`; `insert` e lote não repetem; teto de tempo respeitado; `outcome_unknown` em timeout de escrita.
- [ ] **T-107** **Contratos** (`contracts/`): logger, `TableRepository`, `FileStore`, transportes do adapter, resultados (`Page`, `BatchResult`, `DeleteResult`, `StoredFile`, `CompositeResult`). Dep: T-101. *Critério:* sem dependências externas; teste de arquitetura.
- [ ] **T-108** **Fakes** em `tests/fakes/` (tabelas em memória, storage em memória, relógio, logger de captura) e a **bateria de contrato** reutilizável. Dep: T-107. Ref: 04 §5.2, §11.
- [ ] **T-109** **Testes de arquitetura:** nada fora de `adapters/` importa SDK/`httpx`; `tables/` e `storage/` não se importam; nenhum import da integração antiga; `os.environ` só no módulo de fonte; sem singleton global. Dep: T-002. Ref: 04 §11, 03 §12.

## Fase 2: frente A, tabelas

- [ ] **T-201** **Descritor de tabela, entidades e serialização** (dict e modelo tipado, tipos Postgres, timestamps sem fuso recusados, id uuid). Dep: T-107. Ref: 06 §2–§8.
- [ ] **T-202** **Query Object:** filtro em árvore, ordenação, seleção, operadores v1, validação por allowlist de tabelas/colunas/operadores, recusa de filtro vazio em update/delete. Dep: T-201. Ref: 06 §4, 05 §6.
- [ ] **T-203** **Adapter de tabelas** sobre o SDK: tradução de `Query` para PostgREST e erro bruto normalizado. Dep: T-105, T-202, T-005. Ref: 06 §4.3.
- [ ] **T-204** **Classe de tabelas:** CRUD, upsert e semântica de não encontrado (A-01), declarando idempotência por método. Dep: T-106, T-202. Ref: 02 §11.2, 06. *Critério:* bateria de contrato passa no fake e no adapter.
- [ ] **T-205** **Paginação e iteração:** `Page`, offset padrão, keyset opcional por descritor, contagem opcional, `iterate`, sem truncar em silêncio no limite do servidor. Dep: T-204. Ref: 09 §4–§7, decisão C-2.
- [ ] **T-206** **Lote:** chunks, modos `stop`/`continue`, `BatchResult` por item, retry só se idempotente. Dep: T-204. Ref: 09 §3.
- [ ] **T-207** Testes de integração da frente A contra o projeto de teste (marcador `integration`, `env_guard`, prefixos, limpeza). Dep: T-204, T-205, T-206, T-001. Ref: 04 §6.

## Fase 3: frente B, arquivos (pode andar em paralelo com a Fase 2)

- [ ] **T-301** `[P]` **Validadores:** sanitização de caminho (path traversal), tamanho, extensão, MIME e magic bytes (divergência recusa). Dep: T-107. Ref: 05 §7, 07 §4–§5.
- [ ] **T-302** `[P]` **Nomeação e colisão:** estratégia padrão (data + UUID), nome original saneado como metadado, políticas `reject`/`version`/`overwrite`. Dep: T-107. Ref: 07 §6–§7.
- [ ] **T-303** **Adapter de storage** (upload padrão e resumable, download em stream, URLs pública/assinada, listagem, remoção) com erro bruto normalizado. Dep: T-105, T-005. Ref: 07 §3, §9–§11.
- [ ] **T-304** **Classe de arquivos:** `FileStore` completo, escolha do modo por tamanho, `FileSource` (caminho/bytes/stream), teto de memória, TTL de URL assinada limitado, transferência fora do event loop. Dep: T-106, T-301, T-302. *Critério:* bateria de contrato passa no fake e no adapter.
- [ ] **T-305** **Listagem paginada e exclusão** (um, lote, prefixo). Dep: T-304. Ref: 07 §10–§11, 09 §9.
- [ ] **T-306** Testes de integração da frente B, incluindo **arquivo grande** (marcador `integration`, bucket de teste). Dep: T-304, T-305, T-001. Ref: 04 §6.

## Fase 4: fachada, factory e wrapper assíncrono

- [ ] **T-401** **Fachada** `SupabaseIntegration`: delegação para `tables` e `storage` e as operações combinadas com ordem fixa, compensação de melhor esforço, `CompositeResult` e log `orfao_possivel`. Dep: T-204, T-304. Ref: 08. *Critério:* a fachada não reembrulha exceções (mesma identidade); cenários F1–F8 do 08.
- [ ] **T-402** **Factory:** valida configuração, monta logger, executor, adapters, classes e fachada; aceita substituições; provedor de credencial injetável (C-5). Dep: T-104, T-106, T-203, T-303, T-401. *Critério:* configuração incompleta falha aqui, listando só nomes.
- [ ] **T-403** **Wrapper assíncrono por thread** (`AsyncIntegration`) com limite de transferências simultâneas. Dep: T-402. Ref: 07 §13.
- [ ] **T-404** Testes e2e pela fachada contra o projeto de teste. Dep: T-402, T-207, T-306. Ref: 04 §2.

## Fase 5: qualidade, segurança e fechamento

- [ ] **T-501** Rodar a suíte completa com cobertura (piso 90% linhas, 80% ramos nos testes offline) e corrigir lacunas. Dep: T-404. Ref: 04 §12.
- [ ] **T-502** Revisão de segurança com a checklist de [research/05](research/05-seguranca-de-dados.md) §11 e o teste de "segredo plantado" ponta a ponta. Dep: T-404.
- [ ] **T-503** Verificar os critérios de sucesso da [spec](spec.md) §7 e os critérios de aceite de cada pesquisa (02 §14, 03 §12, 04 §14, 05 §12, 06 §13, 07 §15, 08 §11, 09 §12). Dep: T-501, T-502.
- [ ] **T-504** **Documentação de uso** (US-12): README curto e exemplos de uso da fachada, no padrão de documentação do repositório. Só agora, com o projeto completo. Dep: T-503.
- [ ] **T-505** Validar as URLs de "Referências" de [research/](research/) e anotar as que não confirmarem. Dep: T-005.

## Fase 6 (futura, outra spec): integração com o projeto

Substituir ou conviver com a integração antiga, ajustar `web_services`/agentes, planejar migração. **Fora desta spec** (P1).

---

## Ordem sugerida de execução

```
Fase 0 ─▶ Fase 1 ─┬─▶ Fase 2 (tabelas) ─┐
                  └─▶ Fase 3 (arquivos)─┴─▶ Fase 4 ─▶ Fase 5
```

Caminho mínimo para uma primeira entrega usável: T-000…T-006 → T-101…T-109 → T-201…T-204 e T-301…T-304 → T-401…T-402.
