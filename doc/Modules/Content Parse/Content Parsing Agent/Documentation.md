# Classe `ContentParsingAgent`

## Visão Geral

A classe `ContentParsingAgent` é um agente dedicado a processar dados estruturados de entrada e saída, gerando automaticamente esquemas Pydantic para validação desses dados, além de orquestrar a execução de modelos de linguagem configuráveis para processar o conteúdo conforme instruções fornecidas. Isso permite uma integração fluida entre os dados utilizados e os modelos de inteligência artificial, garantindo consistência e validação rigorosa das informações.

Ela resolve o problema de converter dados brutos em modelos tipados e validados, além de facilitar a execução e o controle de modelos de linguagem com diferentes provedores, como OpenAI ou Groq, sem que o usuário precise lidar diretamente com detalhes internos desses modelos. Na prática, a classe pode ser usada para automatizar pipelines de processamento de dados textuais e geração de conteúdos baseados em regras e configurações definidas, tudo garantindo confiabilidade e rastreabilidade do fluxo.

## Fluxo de Execução

1. **Inicialização**: O usuário cria uma instância do `ContentParsingAgent` passando os dados de entrada e saída como dicionários, além de configurações opcionais.

2. **Geração de Schemas**: Internamente, a classe gera esquemas Pydantic dos dados de input, output e configuração para garantir a validade e tipagem dessas informações.

3. **Configuração do Modelo**: Baseado na configuração, a classe seleciona um modelo de linguagem adequado (ex: OpenAI ou Groq).

4. **Execução do Agente**: Com as instruções, descrição, configurações e schemas prontos, o agente executa o modelo sobre os dados de entrada.

5. **Formatação da Resposta**: A resposta bruta do modelo é formatada para um dicionário estruturado contendo o conteúdo processado, metadados do modelo e métricas da execução, facilitando seu uso ou publicação.

## Tabela de Métodos da Classe

| Método        | Descrição                                               |
|---------------|---------------------------------------------------------|
| `__init__`    | Inicializa o agente com dados de entrada, saída e config.|
| `get_schemas` | Retorna os schemas Pydantic gerados para input, output e configuração.|
| `run_agent`   | Executa o agente com o modelo configurado e retorna a resposta gerada.|
| `format_response` | Formata a resposta bruta do agente em um dicionário estruturado. |

## Variáveis de Ambiente

- Nenhuma variável de ambiente específica é diretamente mencionada, porém a presença do `load_dotenv()` sugere que variáveis podem ser carregadas externamente para configurações (exemplo: chaves de API).

## Pontos Importantes da Arquitetura e Insights

- **Geração Automática de Schemas**: Utiliza classes específicas (`JsonToPydantic`, `GeneratePydanticSchema`) para converter dados genéricos em modelos Pydantic, garantindo validação e tipagem consistente ao longo do fluxo.

- **Flexibilidade no Modelo de Linguagem**: Adota uma abordagem de fábrica simples para retornar diferentes implementações de modelo (OpenAI, Groq) com base nas configurações, o que facilita a extensão para outros provedores.

- **Encapsulamento e Tratamento de Erros**: Centraliza operações críticas (geração de schemas, execução do agente, formatação de resposta) com blocos try-except que convertem erros variados em exceções específicas, aumentando a robustez.

- **Dependências Externas**: Interage com classes externas para modelos (`Agent`, `OpenAIResponses`, `Groq`) e parsing (`Config`, `JsonToPydantic`, `GeneratePydanticSchema`), delegando responsabilidades e mantendo a classe focada no fluxo principal.

---

# Descrição da Classe e Métodos

## Classe `ContentParsingAgent`

### Descrição

Esta classe funciona como um agente intermediário para processar dados estruturados, convertendo-os em modelos Pydantic validados e utilizando modelos de linguagem configurados para processar dados textuais conforme instruções específicas. Ela oferece um pipeline integrado que cobre desde a validação até a execução e formatação da resposta, facilitando integrações com sistemas de IA de maneira segura e modular.

### Argumentos do Construtor

| Argumento    | Tipo                | Descrição                                       | Valor Padrão |
|--------------|---------------------|------------------------------------------------|--------------|
| input_data   | Dict[str, Any]      | Dicionário com os dados de entrada a serem validados e processados.| Nenhum       |
| output_data  | Dict[str, Any]      | Dicionário com os dados de saída esperados após o processamento.    | Nenhum       |
| config_data  | Optional[Dict[str,Any]] | Dicionário opcional contendo configurações do agente.                | None         |

---

### 1. `__init__`

### Descrição

Inicializa o agente com os dados de entrada, saída e configurações opcionais, e imediatamente gera os schemas Pydantic necessários para validar esses dados.

### Argumentos

- `input_data` (Dict[str, Any]): Dados de entrada a serem processados.
- `output_data` (Dict[str, Any]): Dados de saída desejados.
- `config_data` (Optional[Dict[str, Any]]): Configurações adicionais para o agente (opcional).

### Retornos

- Não retorna valor.

### Raises

- Nenhum explicitamente, mas pode levantar RuntimeError durante a geração dos schemas.

### Exemplos

```python
agent = ContentParsingAgent(
    input_data={"nome": "João", "idade": 30},
    output_data={"resultado": "string"},
    config_data={"model_provider": "openai", "model_id": "gpt-4"}
)
```

---

### 2. `get_schemas`

### Descrição

Retorna os schemas Pydantic correspondentes aos dados de entrada, saída e configuração gerados pelo agente.

### Argumentos

- Nenhum.

### Retornos

- dict: Dicionário com as chaves `"input"`, `"output"` e `"config"` contendo seus respectivos schemas.

### Raises

- Nenhum.

### Exemplos

```python
schemas = agent.get_schemas()
print(schemas["input"])
print(schemas["output"])
print(schemas["config"])
```

---

### 3. `run_agent`

### Descrição

Executa o agente utilizando o modelo configurado e as instruções definidas para processar os dados de entrada, retornando a resposta gerada.

### Argumentos

- Nenhum.

### Retornos

- Objeto da resposta gerada pelo modelo, geralmente contendo conteúdo e métricas.

### Raises

- RuntimeError: Caso ocorra um erro durante a execução do modelo.

### Exemplos

```python
response = agent.run_agent()
print(response)
```

---

### 4. `format_response`

### Descrição

Formata a resposta bruta obtida na execução do agente em um dicionário estruturado, extraindo o conteúdo útil, metadados do modelo e estatísticas da execução para fácil consumo.

### Argumentos

- `raw_response`: Objeto de resposta bruta retornado pelo agente.

### Retornos

- dict: Dicionário estruturado com as chaves `"content"` (dados processados) e `"metadata"` (informações do modelo e métricas).

### Raises

- RuntimeError: Caso ocorra erro durante a formatação da resposta.

### Exemplos

```python
formatted = agent.format_response(response)
print(formatted["content"])
print(formatted["metadata"]["model"])
print(formatted["metadata"]["tokens"])

# python -m src.content_parse.content_parsing_agent
```

---

Essa documentação apresenta o `ContentParsingAgent` de maneira didática e estruturada para facilitar o entendimento e uso por desenvolvedores, evidenciando os pontos chave do seu funcionamento e exemplos práticos de aplicação.