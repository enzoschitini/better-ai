# Documentação da Classe `DataframeAgent`

## Visão Geral

A classe `DataframeAgent` oferece uma solução integrada para interagir com pandas DataFrames através de agentes baseados em modelos de linguagem avançados, como OpenAI e Google Gemini. Ela permite que desenvolvedores realizem consultas naturais em seus dados e recebam respostas enriquecidas com análises, gráficos e uso inteligente de ferramentas.

Este agente abstrai toda a complexidade por trás da inicialização dos modelos, incorporação de ferramentas auxiliares, manipulação do prompt (incluindo trechos do DataFrame) e controle detalhado de parâmetros como temperatura, verbosidade e tempo máximo de execução. Na prática, é útil para quem deseja explorar dados de forma conversacional sem escrever código explícito de análise e visualização, acelerando insight e automação em Data Science.

## Fluxo de Execução

1. **Inicialização (`__init__`)**: Cria o agente configurando parâmetros como o modelo, provedor, toolkit de ferramentas, configuração do prompt e parâmetros de execução. Defaults são aplicados via `AgentConfig` para garantir robustez e facilidade de uso.
2. **Configuração do modelo (`_get_model`)**: Baseado no provedor (OpenAI ou Gemini), inicializa e armazena o modelo de linguagem a ser utilizado na comunicação.
3. **Configuração das ferramentas (`_get_tools`)**: Constrói uma lista de ferramentas a partir do toolkit vinculado ao DataFrame, para ampliar a capacidade de consulta do agente.
4. **Criação do agente (`create_agent`)**: Conecta o DataFrame, modelo e ferramentas em um agente pandas customizado, pronto para responder consultas.
5. **Invocação do agente (`invoke`)**: Executa o agente com a consulta do usuário, coleta outputs textuais, gráficos gerados, resultados intermediários e estatísticas detalhadas de tokens usados.
6. **Execução completa (`run_agent`)**: Método que orquestra todo o fluxo acima, simplificando o uso final para que o usuário apenas passe a consulta natural para obter análises completas.

## Tabela de Métodos da Classe

| Método       | Descrição                                                      |
|--------------|----------------------------------------------------------------|
| `__init__`   | Inicializa a instância do agente com configurações e DataFrame.|
| `_get_model` | Inicializa o modelo de linguagem com base no provedor escolhido.|
| `_get_tools` | Cria ferramentas auxiliares baseadas no toolkit fornecido.     |
| `create_agent` | Cria o agente pandas configurado com modelo, ferramentas e parâmetros.|
| `invoke`     | Executa o agente com a consulta do usuário e retorna os resultados.|
| `run_agent`  | Executa o fluxo completo do agente iniciando modelo, ferramentas, agente e processando consulta. |

## Pontos Importantes da Arquitetura e Insights

- **Configuração via `AgentConfig`**: Parâmetros padrão e fallback são gerenciados por uma classe separada, promovendo centralização e facilidade de manutenção.
- **Suporte Multi-Provedor**: O design prevê fácil inclusão de fornecedores adicionais além do OpenAI e Gemini, facilitando extensibilidade.
- **Uso do Toolkit para Ferramentas**: A integração com o toolkit permite estender a inteligência do agente com funções customizadas, mantidas fora da classe principal para modularidade.
- **Patch em Matplotlib para Coleta de Gráficos**: A coleta de gráficos é feita com `PlotCollector`, que intercepta comandos de plotagem, viabilizando a recuperação de visualizações geradas durante a execução.
- **Traçamento e Logs**: A classe emprega o `ApplicationTracing` para registrar operações, erros e estado interno, essencial para debugging e monitoramento.
- **Isolamento do Fluxo**: Métodos internos são discretos e especializados, o que torna o fluxo `run_agent` simples de usar, com delegação robusta de responsabilidades.
- **Manejo personalizado de erros**: Cada etapa crítica lança exceções específicas com logging, facilitando diagnósticos ao integrar o agente em sistemas maiores.

---

# Descrição da Classe e Métodos

## Classe `DataframeAgent`

### Descrição

A `DataframeAgent` encapsula um agente interativo que opera sobre um DataFrame pandas. Ela integra modelos de linguagem de alto nível e um conjunto de ferramentas customizáveis para interpretar consultas, gerar análises e produzir visualizações automaticamente. O agente pode incluir trechos do DataFrame no prompt para enriquecer respostas e aplicar controles granulares sobre a execução, garantindo flexibilidade e segurança.

### Argumentos do Construtor

| Argumento            | Tipo    | Descrição                                                | Valor Padrão           |
|---------------------|---------|---------------------------------------------------------|-----------------------|
| `dataframe`         | DataFrame | O DataFrame pandas a ser analisado                      | - (obrigatório)        |
| `toolkit`           | object  | Conjunto de ferramentas para manipulação do DataFrame    | None                   |
| `id_model`          | str     | Identificador do modelo para o agente                    | Configuração padrão    |
| `model_provider`    | str     | Provedor do modelo (ex: 'openai', 'gemini')              | Configuração padrão    |
| `temperature`       | float   | Temperatura para geração do modelo                        | Configuração padrão    |
| `agent_type`        | str     | Tipo do agente pandas a ser criado                        | Configuração padrão    |
| `include_df_in_prompt` | bool | Se deve incluir linhas do DataFrame no prompt            | Configuração padrão    |
| `number_of_head_rows`  | int   | Quantidade de linhas do DataFrame para incluir            | Configuração padrão    |
| `max_execution_time` | int     | Tempo máximo de execução do agente em segundos            | Configuração padrão    |
| `early_stopping_method` | str  | Método de parada antecipada para execução                  | Configuração padrão    |
| `allow_dangerous_code` | bool  | Permite execução de código potencialmente perigoso         | Configuração padrão    |
| `verbose`           | bool    | Nível de detalhamento das mensagens de log                | Configuração padrão    |
| `prefix`            | str     | Texto prefixo para o prompt do agente                      | Configuração padrão    |
| `suffix`            | str     | Texto sufixo para o prompt do agente                       | Configuração padrão    |

---

### 1. `__init__`

#### Descrição

Inicializa a instância do agente com todos os parâmetros necessários para configurar o modelo, ferramentas e ambiente de execução. Também ativa o coletor de gráficos e registra a configuração inicial via trace.

#### Argumentos

- `dataframe` (DataFrame): DataFrame a ser analisado.
- `toolkit` (object, opcional): Ferramentas para auxiliar nas consultas.
- `id_model` (str, opcional): Identificador do modelo de linguagem.
- `model_provider` (str, opcional): Provedor do modelo.
- `temperature` (float, opcional): Temperatura para geração.
- `agent_type` (str, opcional): Tipo do agente pandas.
- `include_df_in_prompt` (bool, opcional): Incluir dados no prompt.
- `number_of_head_rows` (int, opcional): Número de linhas do DataFrame no prompt.
- `max_execution_time` (int, opcional): Tempo máximo para execução.
- `early_stopping_method` (str, opcional): Método para parada antecipada.
- `allow_dangerous_code` (bool, opcional): Permitir código perigoso.
- `verbose` (bool, opcional): Ativar mensagens detalhadas.
- `prefix` (str, opcional): Prefixo para prompt.
- `suffix` (str, opcional): Sufixo para prompt.

#### Retornos

- Não retorna valor.

#### Raises

- Nenhum explícito.

#### Exemplos

```python
agent = DataframeAgent(dataframe=df, id_model="gpt-4", model_provider="openai", verbose=True)
```

---

### 2. `_get_model`

#### Descrição

Inicializa o modelo de linguagem apropriado com base no provedor configurado, seja OpenAI ou Google Gemini. Valida a escolha do provedor e configura temperatura e credenciais.

#### Argumentos

- `provider` (str, opcional): Nome do provedor; se não fornecido, usa o padrão interno.

#### Retornos

- Instância do modelo configurado para uso pelo agente.

#### Raises

- `RuntimeError`: Se ocorrer erro na inicialização do modelo ou provedor inválido.

#### Exemplos

```python
model = agent._get_model(provider="openai")
```

---

### 3. `_get_tools`

#### Descrição

Cria e inicializa a lista de ferramentas que o agente pode utilizar, baseando-se no toolkit eventualmente passado durante a criação do agente. Se não houver toolkit, retorna lista vazia.

#### Argumentos

- Nenhum.

#### Retornos

- Lista de objetos `Tool` configurados para a interação do agente.

#### Raises

- `RuntimeError`: Se falha ao recuperar as ferramentas do toolkit.

#### Exemplos

```python
tools = agent._get_tools()
for tool in tools:
    print(tool.name)
```

---

### 4. `create_agent`

#### Descrição

Cria o agente pandas propriamente dito, associando o modelo, DataFrame, ferramentas, e parâmetros finos de execução para preparar o ambiente para as consultas.

#### Argumentos

- Nenhum.

#### Retornos

- Instância do agente pandas criada e configurada.

#### Raises

- `RuntimeError`: Se ocorrer erro na construção do agente.

#### Exemplos

```python
agent_instance = agent.create_agent()
```

---

### 5. `invoke`

#### Descrição

Executo o agente com uma consulta fornecida pelo usuário. Captura a resposta textual, gráficos gerados, resultados das ferramentas e estatísticas detalhadas do uso de tokens para análise posterior.

#### Argumentos

- `user_query` (str): Consulta em linguagem natural para ser processada pelo agente.

#### Retornos

- Dicionário contendo:
  - `input`: Entrada original.
  - `output`: Resposta textual do agente.
  - `graphs`: Lista de gráficos gerados.
  - `tool_result`: Resultados de ferramentas (se houver).
  - `usage`: Estatísticas do uso de tokens e custo.

#### Raises

- `RuntimeError`: Se erro durante a invocação do agente.

#### Exemplos

```python
result = agent.invoke("How many passengers are in each class?")
print(result["output"])
for graph in result["graphs"]:
    display(graph)
```

---

### 6. `run_agent`

#### Descrição

Método de mais alto nível para executar o fluxo completo: inicializa o modelo, configura ferramentas, cria o agente e processa a consulta fornecida. Ideal para uso direto, escondendo detalhes da configuração.

#### Argumentos

- `user_query` (str, opcional): Consulta para processamento. Valor padrão é uma instrução de criação de gráfico de barras.

#### Retornos

- Dicionário com a resposta consolidada do agente, incluindo gráficos e informações de uso.

#### Raises

- Propaga exceções lançadas internamente pelas etapas encadeadas.

#### Exemplos

```python
response = agent.run_agent("Create a bar chart showing count of passengers by class.")
print(response["output"])
for fig in response["graphs"]:
    fig.show()
```

---

Esta documentação visa clarear o uso e arquitetura do `DataframeAgent` para desenvolvedores buscando integrar agentes inteligentes e interativos em suas soluções de análise de dados.