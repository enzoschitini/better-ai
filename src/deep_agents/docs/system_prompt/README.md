# Deep Agents: recursos de prompt, um por vez

Cada recurso tem seu próprio `.py`, isolado dos outros, para você validar um de cada vez antes de combiná-los.
Verificado contra `deepagents 0.7.40` (código-fonte instalado) e a documentação da LangChain
([Customize Deep Agents](https://docs.langchain.com/oss/python/deepagents/customization)).

| Arquivo | Recurso | Complexidade |
|---|---|---|
| `01_system_prompt.py` | `system_prompt=` | mínima |
| `05_harness_profile.py` | `HarnessProfile` (prompt que acompanha o modelo) | baixa |
| `03_memory.py` | `memory=` (`AGENTS.md`) | baixa |
| `04_skills.py` | `skills=` (`SKILL.md` sob demanda) | média |
| `06_summarization.py` | `SummarizationMiddleware` + `summary_prompt` | média |
| `02_subagents.py` | `subagents=` | maior |

`_comum.py` tem utilitários dos exemplos (criação do gateway, impressão do relatório e o "espião" de prompt).
`llm_gateway.py` é a sua interface de modelos com métricas, a mesma de antes.

## Como rodar

```bash
pip install -U deepagents "langchain[anthropic]"      # ou o extra do seu provedor
export ANTHROPIC_API_KEY=...                           # chave do provedor escolhido
python 01_system_prompt.py
```

Variáveis opcionais:

- `MODELO=openai:gpt-5.4` troca o modelo (padrão: `anthropic:claude-sonnet-4-6`).
- `MOSTRAR_PROMPT=0` esconde o system prompt exibido (padrão: mostra).
- `PROMPT_MAX=6000` aumenta o limite de caracteres do prompt exibido.

Todo exemplo imprime três coisas: **o system prompt exato que o modelo recebeu na 1ª chamada**, a resposta final e as
métricas (tokens, tempo, ferramentas pedidas e executadas). O prompt exibido mostra, na prática, o que cada recurso
injeta.

---

## 1. `system_prompt=` — instruções do agente principal

**O que é.** Suas instruções para o agente principal. Aceita `str` ou `SystemMessage` (os blocos de conteúdo e marcadores
`cache_control` são preservados).

**Como o prompt final é montado** (do código-fonte do `create_deep_agent`):

```
USER (seu system_prompt)  →  BASE (base_system_prompt do perfil)  →  SUFFIX (system_prompt_suffix do perfil)
```

As partes são separadas por linha em branco. Seu prompt vem **primeiro**.

**Sem `system_prompt` e sem perfil**, o prompt autoral é **vazio**. Eu confirmei isso rodando o agente: o modelo recebeu
um system prompt de 0 caracteres (na versão 0.7.40, o prompt padrão é vazio). Quando
você ativa `memory`, `skills` ou `subagents`, os middlewares correspondentes acrescentam suas próprias seções.

**Quando usar.** Papel, tom, idioma, formato de resposta, regras gerais.

**Observe ao rodar.** O prompt exibido começa com o seu texto, e a resposta deve terminar com "Dica: ...".

---

## 2. `subagents=` — delegação com contexto isolado

**O que é.** O agente principal ganha a ferramenta `task`. Ao chamá-la, ele dispara um subagente que roda em contexto
separado e devolve só o resultado. Isso evita encher o contexto principal com trabalho detalhado.

**Cada subagente (dicionário) aceita:** `name`, `description` (é o que o principal lê para decidir delegar), `system_prompt`
(sempre `str`), `tools` e, opcionalmente, `model` (modelo diferente do principal).

**Pontos de atenção**
- A `description` precisa dizer *quando* delegar. Descrição vaga, delegação que não acontece.
- Subagentes declarativos **não herdam** o middleware que você passou ao agente principal. Passe no campo `middleware` do
  próprio subagente.
- Existe um subagente `general-purpose` adicionado automaticamente (um perfil pode desativá-lo).

**Observe ao rodar.** Nas "chamadas ao modelo", a 1ª pede a ferramenta `task`. Depois aparece a chamada do subagente à
ferramenta de conversão, e em "ferramentas executadas" aparecem `converter_celsius_para_fahrenheit` e `task`. As chamadas
do subagente entram no mesmo relatório de métricas, porque os callbacks se propagam.

---

## 3. `memory=` — `AGENTS.md` sempre carregado

**O que é.** Lista de caminhos de arquivos `AGENTS.md` lidos na inicialização e injetados no prompt. É contexto
**permanente**: convenções, preferências, regras do projeto.

**Pontos de atenção**
- O arquivo precisa existir no **backend** antes de criar o agente. No exemplo, semeamos o `StateBackend` (o padrão)
  mandando `"files": {"/AGENTS.md": create_file_data(...)}` no input. Caminhos virtuais começam com `/`.
- Como o conteúdo vai em toda chamada, memória grande custa tokens em todas elas. Para conhecimento que só às vezes
  importa, prefira skills.
- Usa `checkpointer` e `thread_id`, como na documentação.

**Observe ao rodar.** O texto do `AGENTS.md` aparece dentro do system prompt exibido, e a resposta cita "Dev Atlas".

---

## 4. `skills=` — conhecimento sob demanda

**O que é.** Pastas com um `SKILL.md` (frontmatter `name` + `description`, depois as instruções). Só o nome e a descrição
ficam no prompt. O agente lê o conteúdo completo, com `read_file`, **apenas quando julga a skill útil**. Isso é
"divulgação progressiva": economiza tokens.

**Pontos de atenção**
- A `description` é o gatilho. Escreva dizendo *quando* usar a skill.
- Assim como na memória, os arquivos precisam estar no backend antes de criar o agente.
- O catálogo de skills no prompt pode ser personalizado ou suprimido sobrescrevendo o `SkillsMiddleware`
  (veja "Examples" em *Override a default middleware instance* na documentação).

**Observe ao rodar.** O prompt mostra a skill `resumo-tecnico` só com a descrição. Em "ferramentas executadas" aparece
`read_file`, e a resposta segue o formato definido no `SKILL.md`. Se o modelo não ler a skill, a descrição não foi
convincente o bastante para o pedido.

---

## 5. `HarnessProfile` — ajuste que acompanha o modelo

**O que é.** Um pacote de configuração registrado uma vez e aplicado automaticamente sempre que aquele modelo for
selecionado. Útil porque cada modelo "entende" prompts de um jeito diferente.

**Campos** (todos opcionais; o que você não define fica no padrão). Descrições conferidas no código-fonte de
`deepagents.profiles.harness.harness_profiles` (0.7.x, API marcada como *beta*):

| Campo | Tipo | Para que serve |
|---|---|---|
| `base_system_prompt` | `str \| None` | Slot `BASE` do prompt |
| `system_prompt_suffix` | `str \| None` | Slot `SUFFIX`, no fim do prompt |
| `tool_description_overrides` | `dict[str, str]` | Troca a descrição de ferramentas |
| `excluded_tools` | `frozenset[str]` | Esconde ferramentas do modelo |
| `excluded_middleware` | `frozenset[classe \| str]` | Remove middlewares da pilha |
| `extra_middleware` | `Sequence \| Callable` | Acrescenta middlewares à pilha |
| `general_purpose_subagent` | `GeneralPurposeSubagentProfile` | Ajusta ou desliga o subagente padrão |

#### `base_system_prompt`
Preenche o slot `BASE` (ordem final: `USER → BASE → SUFFIX`). Quando aplicado a uma pilha, **substitui** o prompt-base
autoral dela. No agente principal esse prompt-base é vazio por padrão, então definir este campo **adiciona** texto logo
depois do seu `system_prompt=`. Se um perfil define este campo e também `general_purpose_subagent.system_prompt`, o
segundo vence para o subagente general-purpose. Na maioria dos casos você só precisa do `system_prompt_suffix`.

#### `system_prompt_suffix`
Texto anexado por **último** no prompt, depois do `USER` e do `BASE`, para ficar o mais perto possível do histórico da
conversa. É o campo mais usado para calibrar um modelo ("responda em até 100 palavras", "pense passo a passo"). Vale
para **todas** as pilhas que consultam o perfil: agente principal, subagentes declarativos cujo modelo resolve para
este perfil e o subagente general-purpose. É o que o exemplo `05_harness_profile.py` usa.

#### `tool_description_overrides`
Dicionário `{nome_da_ferramenta: nova_descrição}` que reescreve o que o modelo lê sobre uma ferramenta. Funciona onde há
um ponto estável de troca: ferramentas nativas de arquivos, a ferramenta `task` e ferramentas suas do tipo `BaseTool`
ou dict. **Funções simples (callables) não são alteradas.**
- Chave com nome errado, ou de ferramenta renomeada/removida, **não dá erro**: vira *no-op* silencioso. Confira o nome.
- Ao sobrescrever `"task"`, mantenha o marcador `{available_agents}` no texto. Sem ele, o modelo não vê a lista de
  subagentes e a ferramenta perde utilidade.
- Depois de criado, o perfil é imutável (alterar o dict dá `TypeError`). Para mudar, registre de novo ou crie outro.

#### `excluded_tools`
Conjunto de nomes de ferramentas removidas do que o modelo enxerga. Vale para ferramentas suas e para as que os
middlewares do Deep Agents injetam (por exemplo `execute`). Ao combinar perfis, as exclusões **se somam** (a do provedor
mais a do modelo). É calibragem para o modelo, **não** uma barreira de segurança. Para esconder ferramentas de
`FilesystemMiddleware` ou `SubAgentMiddleware` sem remover o middleware, use este campo.

#### `excluded_middleware`
Conjunto de middlewares a retirar da pilha, como **classe** (casa pelo tipo exato, sem subclasses) ou como **string** com
o `.name` do middleware. Prefira a classe quando ela for importável, porque erro de digitação aparece já no import. A
string serve para perfis em YAML/JSON, e `"SummarizationMiddleware"` funciona como apelido público. O filtro roda sobre a
pilha inteira, inclusive middlewares passados em `create_deep_agent(middleware=[...])`. Restrições:
- `FilesystemMiddleware` e `SubAgentMiddleware` **não podem ser excluídos** (são estrutura obrigatória) e dão
  `ValueError` na criação do perfil.
- Entrada que não casa com nenhum middleware da pilha é **rejeitada** (provável erro de digitação ou perfil velho).
- Strings vazias, com `:` ou começando com `_` dão `ValueError`.

#### `extra_middleware`
Middlewares (instâncias de `AgentMiddleware`) acrescentados a **toda** pilha que o `create_deep_agent` monta: agente
principal, subagente general-purpose e subagentes declarativos. Entram depois dos padrões do SDK e dos que você passou em
`middleware=`, e antes da exclusão de ferramentas do perfil, do cache de prompt, da memória e do human-in-the-loop.
Aceita uma sequência fixa ou uma **função sem argumentos** que devolve a sequência; use a função quando as instâncias não
devem ser compartilhadas entre pilhas. **Não** se aplica a `CompiledSubAgent` nem a `AsyncSubAgent`. Só existe em código:
não faz parte do `HarnessProfileConfig` (YAML/JSON).

#### `general_purpose_subagent`
Recebe um `GeneralPurposeSubagentProfile` que edita o subagente `general-purpose` adicionado automaticamente. Sem
valor, ele roda com a descrição e o prompt padrão. Só afeta esse subagente padrão, e não um que você mesmo nomeie
`general-purpose`. Campos do sub-perfil:
- `enabled`: `None` herda (padrão: ligado), `True` força a inclusão, `False` remove o subagente. Se ele for removido e
  você não passar outros subagentes síncronos em `subagents=`, a ferramenta `task` deixa de existir. É assim que se
  remove a `task`, já que `SubAgentMiddleware` não pode ser excluído.
- `description`: troca a descrição.
- `system_prompt`: troca o prompt do subagente (vence o `base_system_prompt` do perfil).

```python
HarnessProfile(
    system_prompt_suffix="Responda em no máximo 100 palavras.",
    excluded_tools=frozenset({"execute"}),
    tool_description_overrides={"ls": "Lista arquivos do diretório virtual."},
    general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False),
)
```

Para perfis em arquivo, `HarnessProfileConfig` guarda só o subconjunto declarativo (strings, listas, dicts), sem
`extra_middleware` nem `excluded_middleware` em forma de classe, e pode ser passado direto a `register_harness_profile`.

**Chaves de registro**
- `"anthropic"` (só o provedor): vale para todos os modelos do provedor.
- `"anthropic:claude-sonnet-4-6"` (provedor:modelo): vale só para esse modelo e herda do perfil do provedor.

**Funciona com modelo já instanciado?** Sim. Eu conferi: com `init_chat_model("anthropic:claude-sonnet-4-6")` (instância
pronta, como o seu `LLMGateway` faz), o perfil registrado com essa chave foi encontrado. O código-fonte resolve o perfil
pelo provedor e pelo identificador do modelo. Isso corrige a minha cautela de antes. Já o *provider profile*
(`register_provider_profile`, que define argumentos de construção) **não** se aplica a instâncias prontas.

**Pontos de atenção**
- A chave precisa casar com o provedor/modelo reportado pela instância. Se o perfil não aparecer no prompt, comece
  conferindo a chave.
- `system_prompt=` do agente vem **antes** do sufixo do perfil (ordem `USER → BASE → SUFFIX`).

**Observe ao rodar.** O prompt exibido termina com "REGRA DO PERFIL: ...".

---

## 6. `SummarizationMiddleware` — o prompt do resumo

**O que é.** Quando o histórico passa de um limite, as mensagens antigas viram um resumo e o contexto continua enxuto.
Você controla o limite (`trigger`), o que fica intacto (`keep`) e o texto que guia o resumo (`summary_prompt`).

**Parâmetros usados no exemplo**
- `trigger=("messages", 6)` dispara a partir de 6 mensagens (o padrão é bem maior; baixei só para você ver acontecer).
  A assinatura também aceita outros tipos de limite, como tokens ou fração do contexto.
- `keep=("messages", 2)` mantém as 2 mensagens mais recentes.
- `summary_prompt` é o seu texto e **precisa conter `{messages}`**.
- `model` pode ser um modelo mais barato só para resumir.

**Pontos de atenção**
- Passar um `SummarizationMiddleware` **substitui** o padrão (casa pelo `.name`), não soma. Configure `model` e `backend`
  por completo.
- Agentes de turno único raramente chegam ao gatilho. Aqui o script faz 5 turnos na mesma `thread_id`.

**Observe ao rodar.** No turno em que o limite é atingido, o script mostra uma chamada a mais ao modelo (a do resumo).
Na última pergunta, o agente deve ainda saber o nome do projeto e a hospedagem, porque o resumo preserva isso. Se errar, o `summary_prompt` não está retendo fatos importantes.

---

## Ordem sugerida para estudar

1. `01` → vê o prompt puro funcionando.
2. `05` → vê o prompt crescer sem mexer no agente.
3. `03` e `04` → compara contexto permanente (`memory`) com contexto sob demanda (`skills`) e o que cada um custa em tokens.
4. `06` → vê o contexto sendo comprimido.
5. `02` → só depois, a delegação.

Depois disso, a combinação é só passar vários argumentos juntos ao mesmo `create_deep_agent`.

## O que foi testado

Rodei os exemplos 01, 02, 03, 04 e 06 com um modelo falso (sem rede, sem chaves): o prompt chegou ao modelo, a memória
e o catálogo de skills apareceram no prompt, a ferramenta `task` foi pedida e executada, o subagente rodou sua
ferramenta, `read_file` foi acionado na skill e o resumo gerou a chamada extra. O exemplo 05 foi verificado pela
resolução do perfil com uma instância real do `ChatAnthropic`. **Nenhum foi executado com um modelo real**, então o
comportamento do modelo (por exemplo, se ele decide ler uma skill) você valida no seu ambiente.
