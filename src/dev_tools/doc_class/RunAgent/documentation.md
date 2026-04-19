# Classe `RunAgent`

## Visão Geral

A classe `RunAgent` é projetada para gerenciar e executar operações relacionadas a um agente inteligente, facilitando a interação com o agente por meio de métodos para depuração, geração de respostas formatadas em JSON, e exposição do agente via uma interface web utilizando o `AgentOS`. Ela integra funcionalidades para lidar com inputs textuais, formatar saídas e servir o agente em uma aplicação web simples, simplificando o uso e testes do agente em diferentes contextos.

Seu principal problema resolvido é o gerenciamento prático das operações do agente, fornecendo métodos claros e reutilizáveis para executar o agente, visualizar suas respostas de maneira estruturada, e disponibilizá-lo como um serviço web. Na prática, pode-se usá-la para desenvolver aplicações que necessitam de respostas automatizadas do agente, testar fluxos de forma detalhada, ou construir protótipos rápidos com interface web para o agente.

`python -m src.agents.ultils.test_agents.run_agent`

## Fluxo de Execução

1. **Inicialização:** Cria uma instância de `RunAgent` passando um objeto `Agent` configurado (ex: modelo e parâmetros de debug).
2. **Depuração:** Chama o método `debug` com uma string de entrada para imprimir diretamente a resposta do agente para essa solicitação.
3. **Resposta JSON:** Usa o método `js_reponse` para enviar uma string ao agente, formatar a resposta em JSON, salvar em um arquivo `.json`, imprimir a resposta formatada e, opcionalmente, mostrar metadados de ferramentas associadas.
4. **Servir via AgentOS:** Chama o método `agent_os` para criar e iniciar uma aplicação web baseada no `AgentOS`, configurando servidor HTTP para que o agente possa ser acessado remotamente, com parâmetros personalizáveis como ID, nome, descrição, host e porta.

## Tabela de Métodos da Classe

| Método     | Descrição                                                  |
|------------|------------------------------------------------------------|
| `__init__` | Inicializa o gerenciador com uma instância de `Agent`.    |
| `debug`    | Imprime a resposta do agente para uma pergunta especificada.|
| `js_reponse` | Executa o agente com texto de entrada e retorna resposta formatada em JSON, salvando em arquivo opcionalmente. |
| `agent_os` | Configura e inicia um servidor web com o agente via `AgentOS`. |

## Pontos Importantes da Arquitetura e Insights

- A classe utiliza **composição**, isto é, ela recebe um objeto `Agent` para delegar as chamadas, mantendo-se desacoplada da implementação interna do agente.
- Usa o padrão **Wrapper/Facade** para simplificar e agrupar operações relacionadas ao agente em uma interface coesa.
- A resposta do agente é tratada com auxílio de classes auxiliares: `FormatAgentResponse` para formatação e `ToolResponse` para metadados, proporcionando modularidade.
- A aplicação web é criada via `AgentOS`, abstração que facilita expor agentes como serviços REST/HTTP sem necessidade de construir infraestrutura web do zero.
- O uso do `pydantic.BaseModel` no método `js_reponse` para validar e estruturar o input evidencia preocupação com robustez.
- O carregamento das variáveis de ambiente com `load_dotenv()` indica possível configuração externa, embora não diretamente usada na classe apresentada.

# Descrição da Classe e Métodos

## Classe `RunAgent`

### Descrição

Classe responsável por gerenciar e executar operações em um agente de inteligência artificial, oferecendo formas práticas para depuração, obtenção de respostas estruturadas em JSON, e disponibilização do agente via servidor web com `AgentOS`.

### Argumentos do Construtor

| Argumento | Tipo  | Descrição                         | Valor Padrão |
|-----------|-------|---------------------------------|--------------|
| `agent`   | Agent | Instância do agente a ser gerenciado | Nenhum      |

### Métodos

---

### 1. `__init__`

### Descrição

Inicializa uma instância da classe `RunAgent` associando-a a um agente específico para gerenciamento.

### Argumentos

- agent (Agent): O objeto agente que será controlado pela instância.

### Retornos

Não retorna valor.

### Raises

Nenhum.

### Exemplos

```python
run_agent = RunAgent(agent=meu_agent)
```

---

### 2. `debug`

### Descrição

Executa uma chamada ao agente imprimindo diretamente a resposta gerada a partir de um texto de entrada padrão ou personalizado.

### Argumentos

- ask (str): Texto de entrada para o agente. Valor padrão é `"Hello!"`.

### Retornos

Não retorna valor.

### Raises

Nenhum.

### Exemplos

```python
run_agent.debug("Qual é a previsão do tempo para hoje?")
# Espera-se que imprima a resposta correspondente do agente no console.
```

---

### 3. `js_reponse`

### Descrição

Executa o agente com um texto de entrada, formata a resposta para JSON, salva essa resposta em um arquivo (se um caminho for fornecido ou padrão), imprime a resposta formatada, e opcionalmente imprime metadados de uma resposta de ferramenta associada.

### Argumentos

- ask (str): Texto de entrada para o agente. Valor padrão é `"Hello!"`.
- path (str): Caminho para salvar o arquivo JSON. Padrão é `"src/agents"`.
- tool_response (ToolResponse): Instância opcional para imprimir informações sobre respostas de ferramentas. Padrão é `None`.

### Retornos

- dict: Dicionário contendo a resposta formatada do agente, pronto para ser convertido em JSON.

### Raises

Nenhum.

### Exemplos

```python
resposta = run_agent.js_reponse(
    ask="Explique a teoria da relatividade",
    path="resultados",
    tool_response=tool_resp_obj
)

print(resposta["content"])  # Exibe o conteúdo da resposta do agente
```

---

### 4. `agent_os`

### Descrição

Configura e inicia um servidor web que disponibiliza o agente por meio de uma aplicação construída com `AgentOS`, permitindo a interação externa via HTTP.

### Argumentos

- id (str): Identificador único da aplicação do agente. Padrão `"my_agent"`.
- name (str): Nome exibido do agente na aplicação. Padrão `"My Agent"`.
- description (str): Descrição do agente. Padrão `"An agent created for demonstration purposes."`.
- host (str): Endereço de host para o servidor. Padrão `"localhost"`.
- port (int): Porta para o servidor. Padrão `7777`.

### Retornos

Não retorna valor.

### Raises

Nenhum.

### Exemplos

```python
run_agent.agent_os(
    id="agent_demo",
    name="Demo Agent",
    description="Agent for demo purposes",
    host="0.0.0.0",
    port=8080
)
# O servidor é iniciado e fica aguardando requisições no endereço especificado.
```