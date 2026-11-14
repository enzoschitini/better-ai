# Registro de decisões

Consolida e resolve as "Questões em aberto" de [research/](research/) e as **contradições** entre os documentos de pesquisa. Em caso de divergência, **este arquivo prevalece**.

**Legenda de status**
- ✅ **Adotada:** consenso entre os documentos de pesquisa e baixo risco. Vale como padrão até alguém contestar.
- ❓ **Confirmar:** depende do usuário. Há uma recomendação, mas a **Fase 0** de [tasks.md](tasks.md) só fecha com sua confirmação.

## 1. Decisões que precisam da sua confirmação (Fase 0)

| ID | Decisão | Recomendação | Alternativa | Status |
|---|---|---|---|---|
| D-01 | **SDK ou REST direto** | SDK oficial `supabase-py` atrás do adapter (já é dependência: `supabase~=2.27.3`). O mapeamento de erros usa status/`code` normalizados, então trocar para REST depois só afeta `adapters/`. | REST direto (PostgREST + Storage) | ❓ |
| D-02 | **Síncrono ou assíncrono** | **Contratos síncronos** + wrapper assíncrono por thread (`asyncio.to_thread`). Motivos: `supabase-py` tem cliente síncrono, o upload resumable (TUS) em Python é síncrono, e o wrapper cobre o uso em FastAPI sem bloquear o event loop. | Contratos assíncronos nativos | ❓ |
| D-03 | **Prefixo das variáveis** | Nomes próprios `SBX_*` (isolados dos `SUPABASE_*` da integração antiga). Fallback legado opcional, **desligado** por padrão e proibido em homol/prod. | Reutilizar `SUPABASE_*` | ❓ |
| D-04 | **Primeiros casos de uso reais** (quais tabelas, colunas e buckets; visibilidade dos buckets) | Definir antes da Fase 3. Alimenta as allowlists, os descritores de tabela e a política de URLs. Até lá, os buckets são tratados como **privados**. | n/a | ❓ |
| D-05 | **Plano do Supabase e limites reais** (limite global de upload, `max-rows`, rate limits) | Levantar na plataforma, **somente leitura**, via [research/01](research/01-variaveis-de-ambiente.md). | n/a | ❓ |
| D-06 | **Um projeto Supabase por ambiente** (dev/homol/prod) e projeto dedicado de testes | Sim: projetos, chaves e `.env` separados; nunca chave de produção em dev. | Um projeto só, separado por schema/bucket | ❓ |
| D-07 | **Nome do pacote Python interno** | `supabase/bai_supabase/` (evita sombrear o SDK `supabase`). A pasta `supabase/` não ganha `__init__.py`. Testes rodam com `pythonpath = supabase`. | Outro nome | ❓ |
| D-08 | **Adicionar `pytest` (e plugins) ao grupo `dev` do `pyproject.toml`** | Sim, isolado em `supabase/tests/`, sem exigir adoção no resto do projeto. | Script ad-hoc como no resto do repo | ❓ |

## 2. Contradições entre os documentos e como foram resolvidas

| ID | Conflito | Resolução | Status |
|---|---|---|---|
| C-1 | **Compensação em operações combinadas:** [02](research/02-tratamento-de-erros-e-resiliencia.md) diz "sem compensação no MVP, só `partial_success`"; [06](research/06-modelagem-de-dados.md)/[08](research/08-consistencia-entre-frentes.md) dizem "compensação simples na fachada". | **Vale o 08** (o documento dedicado): ordem fixa de operações + **compensação de melhor esforço** nos dois casos simples; se a compensação falhar, **não propaga segundo erro**, apenas log `ERROR` com `orfao_possivel=true`. O resultado é `completa`/`parcial`/`falhou` (o "`partial_success`" do 02 vira o resultado `parcial`). | ✅ |
| C-2 | **Paginação:** [09](research/09-lote-e-paginacao.md) recomenda keyset como padrão; [06](research/06-modelagem-de-dados.md) recomenda offset na v1. | **Offset/limit é o padrão da v1** (funciona em qualquer tabela). **Keyset é opcional**, habilitado quando o descritor declara chave de ordenação estável e não nula, e é usado por `iterate` em varreduras grandes. Reavaliar após D-04. | ✅ |
| C-3 | **TTL de URL assinada:** [03](research/03-configuracao-centralizada.md) padrão 3600 s; [05](research/05-seguranca-de-dados.md) padrão 300 s e teto 3600 s. | **Vale o 05** (segurança): padrão **300 s**, teto **3600 s**. Parâmetros: `SBX_STORAGE_SIGNED_URL_TTL_SECONDS=300` e `SBX_STORAGE_SIGNED_URL_MAX_TTL_SECONDS=3600`. | ✅ |
| C-4 | **Retry:** [02](research/02-tratamento-de-erros-e-resiliencia.md) usa `max_attempts` (total, padrão 3); [03](research/03-configuracao-centralizada.md) usa `MAX_RETRIES` (tentativas extras, padrão 3). | Um único parâmetro: **`SBX_RETRY_MAX_ATTEMPTS`** = total de tentativas (padrão 3, onde 1 = sem retry). Substitui `SBX_MAX_RETRIES`. | ✅ |
| C-5 | **Modo de credencial:** [03](research/03-configuracao-centralizada.md) só chave secreta; [05](research/05-seguranca-de-dados.md) oferece também modo `restricted` (publishable). | **v1 usa só a chave secreta** (backend). A Factory recebe um **provedor de credencial** injetável para permitir o modo `restricted` como extensão futura, sem implementá-lo agora. | ✅ |
| C-6 | **Prefixo das variáveis de teste:** [04](research/04-estrategia-de-testes.md) usa `SUPABASE_TEST_*`; [03](research/03-configuracao-centralizada.md) usa `SBX_*`. | Seguir D-03: **`SBX_TEST_*`**, para não colidir com os `SUPABASE_*` legados. `.env.test` (ignorado pelo Git) e `.env.test.example` (só nomes). | ✅ (acompanha D-03) |
| C-7 | **Timeouts:** [02](research/02-tratamento-de-erros-e-resiliencia.md) tem tabela por tipo de operação; [03](research/03-configuracao-centralizada.md) tem chaves únicas (`HTTP_TIMEOUT`, `UPLOAD_TIMEOUT`). | As chaves do 03 são a **configuração base**; a tabela do 02 define os **padrões por categoria** de operação (tabela, lote, arquivo), todos sobrescrevíveis. Ajustar valores com medições reais em homologação. | ✅ |
| C-8 | **Tamanhos de página:** 03 (50, teto 1000), 07 (100 para listagem de objetos do Storage), 09 (limite do servidor 1000). | Tabelas: padrão 50, teto `min(1000, server_max_rows)`. Storage: padrão 100. São contextos diferentes; sem conflito real. | ✅ |

## 3. Decisões adotadas dos documentos de pesquisa (resumo)

| ID | Decisão | Origem |
|---|---|---|
| A-01 | `get_by_id` inexistente → `RecordNotFoundError`; busca vazia → lista vazia; update de inexistente → `RecordNotFoundError`; delete de inexistente → sucesso idempotente informando `removed=false`; lote vazio → `ValidationError`. | [02](research/02-tratamento-de-erros-e-resiliencia.md) §11, [04](research/04-estrategia-de-testes.md) Q8 |
| A-02 | Registros: abordagem híbrida (repositório genérico + descritor de tabela + `dict`). Modelos tipados para tabelas estáveis. | [06](research/06-modelagem-de-dados.md) |
| A-03 | Id padrão `uuid`; soft delete só por opt-in no descritor; timestamps sem fuso são **recusados**; schema configurável por descritor; sem joins na v1. | [06](research/06-modelagem-de-dados.md) Q2, Q3, Q5, Q7 |
| A-04 | Circuit breaker fora da v1, com ponto de extensão (cadeia de políticas injetável). | [02](research/02-tratamento-de-erros-e-resiliencia.md) §9 |
| A-05 | Atributo `outcome_unknown` faz parte do contrato público das exceções; insert simples **não** repete; upsert pode repetir. | [02](research/02-tratamento-de-erros-e-resiliencia.md) §7 |
| A-06 | Upload: padrão até ~6 MB, resumable (TUS) acima; validação de tamanho, extensão, MIME e magic bytes; `reject` na colisão; caminho gerado com UUID; bucket privado por padrão. | [07](research/07-arquivos-grandes-e-storage.md) |
| A-07 | Detecção de tipo com `filetype` (sem libmagic no Windows). Teto de 32 MB de bytes em memória, lote de exclusão 100. A confirmar com teste real. | [07](research/07-arquivos-grandes-e-storage.md) Q7, Q8 |
| A-08 | Referência a arquivo em registro: sempre `bucket` + `path`, nunca a URL. Substituir arquivo = caminho novo + apagar o antigo depois. Sem coluna de estado e sem limpeza automática na v1. | [08](research/08-consistencia-entre-frentes.md) Q1, Q2, Q5, Q7 |
| A-09 | Allowlists de tabelas e buckets **obrigatórias em prod**; `.env` de arquivo só em dev; homol/prod usam variáveis da plataforma; formato de log `json` em prod. | [03](research/03-configuracao-centralizada.md), [05](research/05-seguranca-de-dados.md) |
| A-10 | Sem concorrência entre chunks e sem atomicidade entre chunks na v1; lote usa upsert por chave natural quando precisar de retry. | [09](research/09-lote-e-paginacao.md) |
| A-11 | Ambiente de integração: stack local via Supabase CLI no dia a dia e projeto de teste na nuvem no CI; cores desativadas fora de TTY ou com `NO_COLOR`. | [04](research/04-estrategia-de-testes.md) |
| A-12 | Sem dependência nova para configuração (biblioteca padrão), salvo `filetype`, TUS e as de teste. Pydantic só se já for padrão do projeto (verificar na Fase 0). | [03](research/03-configuracao-centralizada.md) Q4 |
| A-13 | Chaves rotacionadas a cada 90 dias (responsável a definir por você); antivírus fora de escopo. | [05](research/05-seguranca-de-dados.md) |

## 4. Itens a confirmar por teste ou na plataforma (não são decisões)

Registrados para a Fase 0 e para as tarefas de arquivos e lote:
- Classes de exceção exatas do `supabase-py`/`postgrest`/`storage3` na versão do `uv.lock`.
- Sintaxe de `range`/`count` no SDK Python, `listV2` do Storage, limite de itens por remoção em lote, tamanho máximo efetivo do TUS e `limit` padrão da listagem de objetos.
- Teto de expiração de URLs assinadas e configuração de limite de tamanho/MIME por bucket.
- `max-rows` real do projeto; plano e limite global de upload.
- Algumas URLs de "Referências" em [research/](research/) **não foram abertas** pelos autores dos documentos; validar antes de tratá-las como fonte.
