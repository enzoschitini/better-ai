# Variáveis de ambiente do Supabase — Guia de obtenção

> **Material de pesquisa (refinamento técnico).** A visão geral citada aqui como "00" / "visão geral" agora vive em [../spec.md](../spec.md). As "Questões em aberto" deste arquivo estão **consolidadas e resolvidas em [../decisions.md](../decisions.md)**, que prevalece em caso de divergência. Tarefas de implementação: [../tasks.md](../tasks.md).

> **Para o Claude (ou qualquer agente) que for executar este processo:** este arquivo descreve o que precisa ser obtido na plataforma do Supabase e como trazer para o projeto. Leia inteiro antes de agir. Em caso de dúvida, pergunte ao usuário. Nunca invente valores.

## 1. Por que este arquivo existe

A nova integração (ver [spec.md](../spec.md)) precisa de credenciais e endereços do projeto Supabase, que só existem na plataforma. O usuário não sabe de antemão quais são nem onde se obtêm. Este guia define **o que obter, de onde e para onde levar**.

## 2. O que precisa ser obtido

Lista **[PROPOSTA]**; confirmar contra a documentação oficial atual antes de usar, porque o Supabase vem renomeando as chaves.

| Dado | Para que serve | Onde obter na plataforma |
|---|---|---|
| **Project URL** | Endereço base da API do projeto | Project Settings → Data API (ou botão *Connect*) |
| **Chave pública** (`anon` / *publishable*) | Acesso sujeito às regras de RLS | Project Settings → API Keys |
| **Chave secreta** (`service_role` / *secret*) | Acesso total no backend, ignora RLS | Project Settings → API Keys |
| **Nomes dos buckets** | Frente de arquivos | Storage → lista de buckets (e se são públicos ou privados) |
| **Nomes das tabelas e schema** | Frente de tabelas | Table Editor / Database → Tables |
| **String de conexão Postgres** (opcional) | Só se a integração precisar de acesso direto ao banco | *Connect* → Connection string |

Referência oficial: <https://supabase.com/docs/guides/getting-started/quickstarts/flask>

## 3. Como obter

Escolher, nesta ordem de preferência, o meio que estiver disponível na sessão:

1. **Integração com o navegador Chrome (Claude in Chrome)**, que é o meio **preferido** definido pelo usuário. Usar as ferramentas `mcp__claude-in-chrome__*` para acessar <https://supabase.com/dashboard> na sessão já logada do usuário e obter tudo pela plataforma. Se as ferramentas estiverem adiadas, carregá-las com ToolSearch em uma única chamada e começar por `tabs_context_mcp`. Abrir uma aba nova para o Supabase em vez de reutilizar abas existentes do usuário.
2. **Ferramentas MCP do Supabase**, se conectadas. Ex.: `list_projects`, `get_project_url`, `get_publishable_keys`, `list_tables`. Serve de alternativa ou de conferência quando o navegador não estiver disponível.
3. **Passo manual:** se nenhum dos dois funcionar, listar ao usuário exatamente quais telas abrir e o que copiar.

### Regras ao usar o navegador (Chrome)

- Se a conexão com o Chrome não estiver ativa, avisar o usuário para reconectar a extensão em vez de seguir direto para outro meio.
- Evitar qualquer ação que dispare alertas ou diálogos do navegador, pois eles travam a automação.
- Se as ações falharem após 2 ou 3 tentativas, parar e perguntar ao usuário.
- Se a tela pedir login, 2FA ou captcha, **parar e pedir ao usuário**; nunca tentar contornar.
- Confirmar com o usuário **qual projeto** usar antes de ler qualquer chave (a conta pode ter vários).
- **Somente leitura.** Não criar, alterar, pausar ou apagar nada na plataforma (projetos, buckets, tabelas, políticas) sem pedido explícito. Se algo estiver faltando (ex.: bucket inexistente), **informar** em vez de criar.
- Não gerar nem rotacionar chaves.

## 4. Para onde levar

- Destino: o arquivo **`.env`** na raiz do repositório. Ele já está no `.gitignore` e **nunca deve ser commitado**.
- O `.env` atual **já contém variáveis `SUPABASE_*`** (`SUPABASE_URL`, `SUPABASE_SECRET_KEY` e outras) usadas pela integração antiga. Portanto:
  - **Não sobrescrever nem remover** nenhuma variável existente.
  - **Não ler nem exibir valores** existentes; olhar apenas os nomes.
  - Definir com o usuário se a integração nova **reutiliza** os mesmos nomes ou usa **nomes próprios** (ver questões em aberto). Até lá, só acrescentar o que faltar.
- Criar também (ou atualizar) um **modelo só com os nomes** (sem valores) para documentar o que o projeto espera. Este pode ser versionado.

## 5. Regras de segurança (obrigatórias)

- **Nunca** colar chaves em arquivos versionados, em documentação, em logs, em mensagens de commit ou na conversa.
- Ao relatar o resultado ao usuário, citar apenas os **nomes** das variáveis e se foram preenchidas, nunca os valores.
- A chave secreta (`service_role`) é de uso **exclusivo do backend**; jamais deve ir para frontend ou ser exposta em resposta de API.
- Se uma chave aparecer em algum lugar indevido, avisar o usuário para rotacioná-la.

## 6. Resultado esperado

Ao final, o agente entrega ao usuário um relatório curto:

- Projeto Supabase utilizado (nome).
- Variáveis que foram acrescentadas ao `.env` (**só os nomes**).
- Buckets e tabelas encontrados (nomes, e visibilidade dos buckets).
- O que ficou pendente ou exigiu ação manual.

## 7. Questões em aberto

1. Reutilizar os nomes `SUPABASE_*` já existentes ou usar nomes novos e isolados para a integração nova?
2. A integração usará a chave pública, a secreta, ou as duas (por exemplo, secreta para o backend e pública para URLs de leitura)?
3. Há mais de um ambiente (dev, homologação, produção) com projetos Supabase distintos? Cada um precisa do seu conjunto de variáveis.
4. A string de conexão Postgres será necessária, ou o acesso será só via API?
