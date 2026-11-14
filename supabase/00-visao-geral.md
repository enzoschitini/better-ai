# Integração com Supabase — Visão Geral e Planejamento

> Status: **rascunho inicial de planejamento** (nenhum código escrito ainda).
> Este documento organiza o escopo descrito na conversa inicial. Itens marcados como **[PROPOSTA]** são sugestões a validar; itens em **Questões em aberto** precisam de decisão.

## 1. Contexto e motivação

O repositório já possui uma integração com o Supabase que funciona (tabelas do banco e armazenamento de arquivos), mas apresenta falhas e margem para melhoria.

A decisão é **não evoluir nem reaproveitar essa implementação**. Será construída uma integração nova, do zero, isolada nesta pasta (`supabase/`), sem dependência de código da implementação atual.

## 2. Objetivo

Oferecer ao backend uma integração completa e bem estruturada com o Supabase, em duas frentes:

| Frente | Escopo |
|---|---|
| **A. Tabelas (banco)** | CRUD completo: inserir, criar, editar, atualizar, deletar e buscar registros. |
| **B. Arquivos (storage)** | Salvar, recuperar e deletar arquivos em buckets do Supabase. Qualquer tipo: imagem, áudio, vídeo, documento etc. |

O consumidor da integração é o **backend** (não o usuário final diretamente).

## 3. Princípios de design

A integração será construída com design patterns, expondo contratos (interfaces) e escondendo detalhes do SDK do Supabase.

- **Interface (contrato):** o backend depende de abstrações, nunca do cliente Supabase concreto.
- **Factory:** criação centralizada e configurável dos clientes/serviços.
- **Adapter:** isola o SDK do Supabase atrás do contrato, para que uma troca de SDK/provedor não afete o resto do sistema. *(usar se necessário)*
- **[PROPOSTA]** Separação por responsabilidade: uma frente (tabelas) não conhece a outra (arquivos); ambas compartilham apenas configuração/conexão.
- **[PROPOSTA]** Erros próprios do domínio (ex.: registro não encontrado, falha de upload) em vez de vazar exceções do SDK.

## 3.1 Arquitetura de classes (três classes principais)

A integração é composta por **três classes**, cada uma com uma responsabilidade clara:

| Classe (nome provisório) | Responsabilidade |
|---|---|
| **Classe de tabelas** (ex.: `SupabaseTables`) | Encapsula todo o CRUD de tabelas: inserir, buscar, atualizar, deletar. |
| **Classe de arquivos** (ex.: `SupabaseStorage`) | Encapsula toda a manipulação de buckets: salvar, recuperar, deletar arquivos. |
| **Classe integradora** (ex.: `SupabaseClient`) | Combina as duas anteriores e expõe **um único ponto de entrada** para todo o fluxo do Supabase. Não implementa lógica de tabela ou storage; apenas compõe e delega. |

```
            ┌─────────────────────┐
 backend ──▶│  Classe integradora │  (fachada única)
            └──────────┬──────────┘
              compõe   │   compõe
            ┌──────────┴──────────┐
            ▼                     ▼
   ┌────────────────┐   ┌────────────────┐
   │ Classe tabelas │   │ Classe arquivos│
   └───────┬────────┘   └───────┬────────┘
           ▼                    ▼
        (SDK / conexão Supabase, via adapter)
```

**Requisito central: flexibilidade.** A estrutura deve permitir boa manutenção e evolução sem ficar engessada. Para isso, o design segue SOLID e design patterns:

- **S — Responsabilidade única:** tabelas, arquivos e integração ficam em classes separadas.
- **O — Aberto/fechado:** novos comportamentos (outro tipo de armazenamento, nova regra de busca) entram por extensão, sem editar o que já funciona.
- **L — Substituição de Liskov:** qualquer implementação de um contrato pode ser trocada por outra (inclusive um fake em testes) sem quebrar quem usa.
- **I — Segregação de interfaces:** contratos pequenos e específicos (um para tabelas, outro para arquivos), sem forçar dependência de métodos não usados.
- **D — Inversão de dependência:** a classe integradora recebe as outras duas por **injeção de dependência** e depende de interfaces, não de classes concretas.

Patterns previstos: **Facade** (classe integradora), **Factory** (montagem das três classes e do cliente), **Adapter** (isolar o SDK), **Dependency Injection** (composição).

## 3.2 Logs

A integração terá um padrão próprio de logs, pensado para depuração no terminal:

- **Nível configurável** (ex.: `INFO`, `ERROR`, `DEBUG`), definido por configuração/variável de ambiente, sem alterar código.
- **Verboso, mas legível:** trazer detalhes úteis (operação, tabela/bucket, identificadores, duração, resultado), sem poluir. O detalhe vem em campos organizados, não em texto solto.
- **Cores por tipo/nível** no terminal (ex.: info, aviso, erro, debug com cores distintas) para facilitar a leitura.
- **Nunca registrar segredos** (chaves, tokens, conteúdo sensível de arquivos ou registros).
- O logger é uma **dependência injetada** (contrato próprio), de modo que as classes não dependam de uma biblioteca específica e os testes possam trocá-lo.

## 3.3 Independência da integração atual

Todo o código novo ficará **dentro desta pasta (`supabase/`)**, totalmente **desacoplado** do que existe hoje no projeto:

- Não importa módulos da integração antiga, e a antiga não importa esta.
- Permite **testar e validar isoladamente** primeiro.
- Só **num segundo momento** será planejada a integração com o restante do projeto (fase separada, com seu próprio planejamento).

## 4. Escopo funcional

### 4.1 Frente A — Tabelas

- Criar/inserir registro (um e em lote)
- Buscar (por id, por filtros, listagem com paginação/ordenação)
- Atualizar/editar registro
- Deletar registro
- **[PROPOSTA]** Upsert

### 4.2 Frente B — Arquivos

- Upload (salvar) de arquivo em um bucket
- Recuperação (download e/ou URL de acesso)
- Exclusão de arquivo
- **[PROPOSTA]** Listagem de arquivos de um bucket/pasta
- Suporte a qualquer tipo de mídia (imagem, áudio, vídeo, documento)

## 5. Fora de escopo (por ora)

- Reaproveitar, migrar ou refatorar a integração Supabase existente.
- Alterações de schema (DDL/migrations) pela integração. **[PROPOSTA]**
- Autenticação de usuários finais (Supabase Auth). **[PROPOSTA]**
- Interface de usuário.

## 6. Estrutura inicial sugerida **[PROPOSTA]**

```
supabase/
├── 00-visao-geral.md        # este documento
├── (docs futuros)           # arquitetura, contratos, decisões
├── contracts/               # interfaces (tabelas e arquivos)
├── adapters/                # implementação sobre o SDK do Supabase
├── factories/               # criação dos clientes/serviços
└── errors/                  # exceções do domínio
```

A estrutura definitiva será fechada na etapa de arquitetura, antes do código.

## 7. Roteiro de planejamento

1. **Visão geral** (este documento)
2. Levantamento de requisitos e questões em aberto (seção 8)
3. Arquitetura: contratos (interfaces), factory, adapter, tratamento de erros
4. Especificação detalhada da Frente A (tabelas)
5. Especificação detalhada da Frente B (arquivos)
6. Plano de implementação e estratégia de testes
7. Implementação (somente após aprovação dos passos anteriores)

## 8. Questões em aberto

1. Qual SDK/cliente Python usar: `supabase-py` oficial ou chamadas diretas (PostgREST / Storage REST)?
2. Chamadas **síncronas ou assíncronas**?
3. Que credencial a integração usa (service role ou anon key) e como ela é carregada/configurada?
4. Como representar tabelas: dicionários genéricos, ou modelos tipados (Pydantic) por tabela?
5. Quais buckets existem e são públicos ou privados? Recuperação de arquivo deve devolver bytes, URL pública ou URL assinada?
6. Há limites de tamanho/tipo de arquivo a validar antes do upload?
7. A integração deve coexistir com a atual durante a transição, ou haverá substituição posterior?
8. Quais tabelas/entidades serão os primeiros casos de uso reais?

## 9. Referências

- Documentação oficial do Supabase, quickstart com Flask: <https://supabase.com/docs/guides/getting-started/quickstarts/flask>

## 10. Premissas assumidas

- O briefing original foi ditado por voz; a pasta correta é `supabase/`.
- O projeto usa Python 3.12 e `uv` para dependências.
- O código novo não importa nada da integração Supabase existente.
