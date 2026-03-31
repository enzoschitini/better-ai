# Classe `ContentParsingAgent`

## Visão Geral

A classe `ContentParsingAgent` é projetada para facilitar o parsing e a validação de conteúdos utilizando esquemas Pydantic gerados dinamicamente a partir de dicionários JSON. Ela gerencia a geração dos esquemas para os dados de entrada, saída e configuração, além de selecionar o modelo de linguagem apropriado (como OpenAI ou Groq) com base nas configurações fornecidas. A classe permite executar um agente que processa os dados conforme as instruções definidas e formata a resposta, enriquecendo-a com métricas e metadados úteis.

Esta classe resolve o problema da validação estruturada de dados e do processamento de conteúdo em conformidade com esquemas definidos, facilitando a integração com diferentes provedores de modelos de linguagem. Na prática, ela pode ser utilizada para criar pipelines robustos que interpretam, validam, e moldam dados conforme regras específicas, retornando respostas ricas em metadados para análise detalhada.

## Fluxo de Execução

1. **Inicialização da Classe:** O usuário fornece os dados de entrada, saída e configuração opcionais, que são armazenados e usados para gerar os esquemas Pydantic correspondentes.  
2. **Geração dos Esquemas:** Com `_generate_schemas`, a classe cria internamente os modelos de validação para input, output e configurações, garantindo estrutura e validação consistente para os dados que circularão no agente.  
3. **Seleção do Modelo:** Através do método `_get_model`, a classe identifica qual provedor de modelo (OpenAI ou Groq) usar, instanciando a classe apropriada com parâmetros baseados nas configurações.  
4. **Execução do Agente:** Com `run_agent`, a classe executa o agente configurado, passando os dados de entrada validados e coletando a resposta do modelo.  
5. **Formatação da Resposta:** O método `format_response` processa a saída bruta do agente, extraindo conteúdo estruturado e informações métricas, retornando um resultado detalhado e prontamente utilizável.

## Tabela de Métodos da Classe

| Método        | Descrição                                                  |
|---------------|------------------------------------------------------------|
| `__init__`    | Inicializa o agente com dados de input, output e config.   |
| `_generate_schemas` | Gera esquemas Pydantic para entrada, saída e configuração. |
| `_get_model`  | Seleciona e instancia o modelo de linguagem apropriado.    |
| `get_schemas` | Retorna os esquemas gerados para input, output e config.   |
| `run_agent`   | Executa o agente utilizando os dados validados.             |
| `format_response` | Formata a resposta do agente incluindo metadados e métricas. |

## Variáveis de Ambiente

- Utiliza `load_dotenv()` para carregar variáveis de ambiente, possivelmente necessárias para as configurações do agente ou do modelo, embora não haja variáveis explicitamente referidas no código apresentado.

## Pontos Importantes da Arquitetura e Insights

- **Geração Dinâmica de Esquemas:** A classe utiliza duas utilidades, `JsonToPydantic` e `GeneratePydanticSchema`, para converter dicionários JSON em modelos Pydantic, permitindo validação estática dos dados de entrada e saída, sem a necessidade de definir manualmente essas classes.  
- **Encapsulamento da Configuração:** A configuração pode ser opcional e é encapsulada num esquema próprio que define parâmetros como o provedor do modelo, instruções e modo debug, promovendo flexibilidade.  
- **Polimorfismo na Seleção de Modelo:** O método `_get_model` implementa simples polimorfismo baseado no atributo `model_provider`, escolhendo dinamicamente o modelo adequado. Isso possibilita fácil extensão para novos provedores.  
- **Separação Clara de Responsabilidades:** Cada método trata de uma etapa distinta do processamento — geração de esquemas, seleção de modelo, execução do agente, formatação do resultado — facilitando testes e manutenção.  
- **Integração com Agno Agent:** A classe depende da classe `Agent` da biblioteca `agno`, demonstrando o uso de agentes inteligentes configuráveis para manipular linguagem natural.  

# Descrição da Classe e Métodos

## Classe `ContentParsingAgent`

### Descrição

A `ContentParsingAgent` é um agente especializado para parsing de conteúdo baseado em esquemas Pydantic, que promove validação rigorosa e processamento estruturado de dados. Ela gerencia o fluxo completo desde a conversão dos dados JSON para modelos tipados, passando pela seleção do modelo de linguagem, execução do agente de parsing e a formatação da saída com informações detalhadas.

### Argumentos do Construtor

| Argumento    | Tipo                    | Descrição                                   | Valor Padrão |
|--------------|-------------------------|---------------------------------------------|--------------|
| input_data   | `Dict[str, Any]`        | Dicionário com dados de entrada para o agente | —            |
| output_data  | `Dict[str, Any]`        | Dicionário que define o esquema esperado de saída | —            |
| config_data  | `Optional[Dict[str, Any]]` | Dicionário opcional com configurações extras do agente | `None`       |

### Métodos

---

### 1. `__init__`

### Descrição

Inicializa a instância do agente com os dados de entrada, saída e, opcionalmente, configuração. Em seguida, gera os esquemas Pydantic correspondentes.

### Argumentos

- input_data (`Dict[str, Any]`): Dados que serão processados como entrada.  
- output_data (`Dict[str, Any]`): Esquema esperado para saída.  
- config_data (`Optional[Dict[str, Any]]`): Configurações adicionais para o agente.

### Retornos

- Não retorna valor.

### Raises

- Não.

### Exemplos

```python
agent = ContentParsingAgent(
    input_data={"title": "Post sobre Python"},
    output_data={"summary": "string", "length": "integer"},
    config_data={"model_provider": "openai", "model_id": "gpt-4"}
)
```

---

### 2. `_generate_schemas`

### Descrição

Gera internamente os modelos Pydantic para validação dos dados de entrada, saída e configuração com base nos dicionários informados.

### Argumentos

- Nenhum.

### Retornos

- Não retorna valor.

### Raises

- `RuntimeError`: caso haja erro durante a geração dos esquemas.

### Exemplos

```python
# Método usado internamente; não utilizado diretamente pelo usuário.
agent._generate_schemas()
```

---

### 3. `_get_model`

### Descrição

Seleciona e instancia o modelo correspondente com base no provedor definido nas configurações — atualmente suporta OpenAI e Groq.

### Argumentos

- Nenhum.

### Retornos

- `OpenAIResponses` ou `Groq`: Objeto do modelo de linguagem a ser usado pelo agente.

### Raises

- `ValueError`: se o provedor especificado for desconhecido ou não suportado.

### Exemplos

```python
model = agent._get_model()
```

---

### 4. `get_schemas`

### Descrição

Retorna os esquemas Pydantic gerados para entrada, saída e configuração, que podem ser usados para inspeção ou validação externa.

### Argumentos

- Nenhum.

### Retornos

- `dict`: Contendo as chaves `"input"`, `"output"` e `"config"` com seus respectivos esquemas.

### Raises

- Não.

### Exemplos

```python
schemas = agent.get_schemas()
print(schemas["input"])
print(schemas["output"])
```

---

### 5. `run_agent`

### Descrição

Executa o agente com o modelo e esquemas configurados, processando os dados de entrada e retornando a resposta bruta.

### Argumentos

- Nenhum.

### Retornos

- Conteúdo da resposta gerada pelo agente (tipo variável conforme modelo).

### Raises

- `RuntimeError`: se ocorrer erro durante a execução do agente.

### Exemplos

```python
response = agent.run_agent()
print(response)
```

---

### 6. `format_response`

### Descrição

Recebe a resposta bruta do agente e a transforma em uma estrutura organizada com o conteúdo modelado e metadados como uso de tokens e duração da execução.

### Argumentos

- raw_response: Resposta crua obtida após a execução do agente.

### Retornos

- `dict`: Com chaves `"content"` e `"metadata"` detalhando o resultado e métricas.

### Raises

- `RuntimeError`: se ocorrer erro ao formatar a resposta.

### Exemplos

```python
formatted = agent.format_response(raw_response)
print(formatted["content"])
print(formatted["metadata"])
```

```bash
{
  "content": {
    "research_code": "NA75038-EC",
    "research_name": "Usabilidade da jornada de Grade de cart\u00f5es",
    "methodology": "LAB - Quali Ep.Mod de usabilidade comum",
    "metric": "N\u00e3o se aplica",
    "responses_count": 6,
    "objective": "Compreender como os clientes entendem e interpretam as ofertas de troca de cart\u00e3o (upgrade, downgrade e equalgrade). Queremos entender atrav\u00e9s da pesquisa como os clientes interagem espontaneamente com a jornada de troca de cart\u00e3o 
e seus recursos (comparador de cart\u00f5es e tela de checkout informativa).",
    "project_description": "A squad de Grade de Cart\u00e3o est\u00e1 trabalhando na evolu\u00e7\u00e3o da jornada de Troca de Cart\u00e3o. Com a nova experi\u00eancia, buscamos construir um motor de ofertas mais inteligente, em que as op\u00e7\u00f5es apresentadas estejam alinhadas \u00e0s necessidades de cada cliente. Al\u00e9m disso, as mudan\u00e7as na jornada t\u00eam como objetivo facilitar a compara\u00e7\u00e3o entre os cart\u00f5es e apoiar a tomada de decis\u00e3o, um ponto que hoje na experi\u00eancia AS IS gera dificuldade. Por isso, queremos realizar um teste de usabilidade com clientes para captar o entendimento do conte\u00fado e navega\u00e7\u00e3o da jornada, para garantir uma experi\u00eancia simples, mas encantadora. Vamos explorar duas vers\u00f5es com carrossel e sem e queremos entender qual vers\u00e3o \u00e9 mais intuitiva para o cliente."      
  },
  "metadata": {
    "model": {
      "provider": "OpenAI",
      "id": "gpt-4.1-mini"
    },
    "metrics": {
      "input_tokens": 946,
      "output_tokens": 255,
      "total_tokens": 1201
    },
    "duration": 6.09
  }
}
```

---

A documentação acima fornece uma visão clara e didática da classe `ContentParsingAgent`, sua finalidade, funcionamento interno e exemplos práticos para facilitar a compreensão e uso por desenvolvedores.