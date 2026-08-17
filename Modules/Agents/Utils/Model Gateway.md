# Classe `ModelGateway`

## Visão Geral

A classe `ModelGateway` atua como uma fábrica unificada e consciente dos provedores para os modelos da biblioteca Agno. Seu principal propósito é abstrair a complexidade das diferentes APIs dos provedores de modelos de linguagem, oferecendo uma interface simples, consistente e segura para criar instâncias desses modelos e agentes que os utilize.

Ela resolve o problema da dispersão e variação nas interfaces dos modelos de diferentes provedores (Anthropic, Google, Groq, OpenAI e variantes OpenAI), permitindo que o desenvolvedor selecione o modelo desejado por meio de uma única classe, que gerencia a criação e validação automática dos parâmetros. Assim, o uso prático da classe simplifica a integração com múltiplos modelos sem a necessidade de conhecer detalhes específicos de cada um.

Na prática, você pode criar um modelo ou agente especificando apenas o nome do provedor e parâmetros relevantes, enquanto a `ModelGateway` lida com o mapeamento para a classe correta e valida os argumentos de forma opcional, evitando erros comuns e promovendo maior produtividade e segurança no desenvolvimento.

## Fluxo de Execução

1. **Instanciar a classe** `ModelGateway`, opcionalmente definindo se deseja validação estrita dos parâmetros (padrão é `True`).

2. **Chamar o método** `create_model` passando o nome do `provider`, opcionalmente o `model_id`, a variante `openai_variant` (se aplicável), e quaisquer outros parâmetros do modelo.

3. A classe **resolve internamente qual construtor usar** mapeando o provider e, se for OpenAI, também a variante, para a classe apropriada do modelo.

4. Se a validação estrita estiver habilitada, a `ModelGateway` **valida se todos os parâmetros fornecidos são válidos**, baseando-se na assinatura do construtor da classe de modelo.

5. A instância do modelo é criada e retornada, pronta para uso.

6. Opcionalmente, pode-se criar um agente com `create_agent`, que chama internamente `create_model` e instancia um objeto `Agent` da biblioteca Agno, configurado com o modelo selecionado e parâmetros adicionais.

7. Para facilitar, existem métodos de conveniência para cada provedor e variante mais comuns, como `anthropic()`, `google()`, `openai_chat()`, entre outros, permitindo criar modelos direto sem precisar especificar o provider manualmente.

## Tabela de Métodos da Classe

| Método               | Descrição                                           |
|----------------------|----------------------------------------------------|
| `__init__`           | Inicializa a instância com controle de validação. |
| `supported_providers`| Retorna os provedores suportados.                   |
| `supported_openai_variants` | Retorna as variantes OpenAI suportadas.         |
| `supported_parameters`| Retorna parâmetros válidos para o modelo.          |
| `create_model`       | Cria e retorna uma instância do modelo escolhido.  |
| `create_agent`       | Cria um agente configurado com o modelo selecionado. |
| `anthropic`          | Cria uma instância do modelo Anthropic Claude.     |
| `google`             | Cria uma instância do modelo Google Gemini.        |
| `groq`               | Cria uma instância do modelo Groq.                  |
| `openai_chat`        | Cria uma instância do modelo OpenAIChat.           |
| `openai_responses`   | Cria uma instância do modelo OpenAIResponses.      |
| `open_responses`     | Cria uma instância do modelo OpenResponses.        |
| `openai_like`        | Cria uma instância do modelo OpenAILike.            |

## Variáveis de Ambiente

Este módulo importa e chama `load_dotenv()` no início, indicando que ele carrega variáveis de ambiente definidas em um arquivo `.env`. Embora a classe em si não use diretamente variáveis de ambiente, os modelos subjacentes provavelmente dependem de chaves API e configurações que são configuradas via ENV. Exemplo comum:

- `OPENAI_API_KEY`: chave API para autenticação com modelos OpenAI.
- `ANTHROPIC_API_KEY`: chave para Anthropic.
- `GEMINI_API_KEY`: credenciais para o serviço Google.
- Outras específicas de cada provedor.

## Pontos Importantes da Arquitetura e Insights

- **Design Factory:** A classe utiliza o padrão factory para criar instâncias dos modelos com base em chaves normalizadas, promovendo extensibilidade e centralização da criação.

- **Alias e Normalização:** Usa dicionários para permitir múltiplos nomes para o mesmo provedor ou variantes OpenAI, melhorando a usabilidade.

- **Validação de Parâmetros:** Inspeciona a assinatura do construtor dos modelos para validar os argumentos recebidos, evitando erros silenciosos.

- **Separação entre Modelo e Agente:** Embora crie modelos, suporta diretamente criar agentes configurados com esses modelos, desacoplando responsabilidades.

- **Dependência da Biblioteca Agno:** Utiliza classes do pacote `agno.models` e `agno.agent.Agent`, portanto é um wrapper especializado para essa stack.

# Descrição da Classe e Métodos

## Classe `ModelGateway`

### Descrição

Responsável por unificar a criação de modelos de diferentes provedores de forma segura e simples. Permite especificar o provedor e variantes (no caso do OpenAI) e criar tanto instâncias de modelos quanto agentes que os utilizam, garantindo que os parâmetros estejam corretos e alinhados com as implementações específicas de cada modelo.

### Argumentos do Construtor

| Argumento          | Tipo  | Descrição                                         | Valor Padrão |
|--------------------|-------|--------------------------------------------------|--------------|
| `strict_validation` | bool  | Flag que habilita validação estrita de parâmetros. Se `True`, parâmetros inválidos causam erro. | True         |

### Métodos

---

### 1. `__init__`

#### Descrição

Inicializa a instância da classe definindo o comportamento de validação dos parâmetros para a criação dos modelos.

#### Argumentos

- `strict_validation` (bool): Ativa/desativa a validação rigorosa dos parâmetros. Padrão `True`.

#### Retornos

- Não retorna valor.

#### Raises

- Nenhum.

#### Exemplos

```python
gateway = ModelGateway(strict_validation=False)
```

---

### 2. `supported_providers`

#### Descrição

Retorna uma lista dos provedores de modelos suportados pela classe.

#### Argumentos

- Nenhum.

#### Retornos

- `Sequence[str]`: Sequência de nomes dos provedores suportados, ex: `("anthropic", "google", "groq", "openai")`.

#### Raises

- Nenhum.

#### Exemplos

```python
print(ModelGateway.supported_providers())
# ('anthropic', 'google', 'groq', 'openai')
```

---

### 3. `supported_openai_variants`

#### Descrição

Retorna as variantes específicas do OpenAI suportadas para seleção de modelo.

#### Argumentos

- Nenhum.

#### Retornos

- `Sequence[str]`: Sequência de variantes OpenAI suportadas, exemplo `("chat", "responses", "open_responses", "like")`.

#### Raises

- Nenhum.

#### Exemplos

```python
print(ModelGateway.supported_openai_variants())
# ('chat', 'responses', 'open_responses', 'like')
```

---

### 4. `supported_parameters`

#### Descrição

Retorna a lista dos nomes dos parâmetros válidos para o construtor de determinado modelo/provedor.

#### Argumentos

- `provider` (str): Nome do provedor (ex. "openai", "google", "anthropic").
- `openai_variant` (str): Variante do OpenAI. Padrão `"chat"`.

#### Retornos

- `List[str]`: Lista dos nomes dos parâmetros aceitos pelo construtor do modelo.

#### Raises

- `ValueError`: Se o provedor ou variante for inválido.

#### Exemplos

```python
params = gateway.supported_parameters(provider="openai", openai_variant="like")
print("temperature" in params)
# True (se for parâmetro válido)
```

---

### 5. `create_model`

#### Descrição

Cria e retorna uma instância do modelo correspondente ao provedor e variante, passando os parâmetros necessários para o construtor. Realiza validação dos argumentos se habilitado.

#### Argumentos

- `provider` (str): Nome do provedor - `"anthropic"`, `"google"`, `"groq"` ou `"openai"`.
- `model_id` (Optional[str]): ID do modelo para sobrescrever o parâmetro `id` do construtor.
- `openai_variant` (str, keyword-only): Variante OpenAI a ser usada, padrão `"chat"`.
- `strict_validation` (Optional[bool], keyword-only): Override para validação estrita no método, ignorando configuração da instância.
- `**kwargs` (Any): Todos os parâmetros adicionais aceitos pelo construtor do modelo.

#### Retornos

- Instância específica do modelo solicitado.

#### Raises

- `ValueError`: Se parâmetros inválidos forem passados (quando validação ativada).
- `ValueError`: Se provedor ou variante OpenAI forem inválidos.

#### Exemplos

```python
model = gateway.create_model(
    provider="openai",
    openai_variant="chat",
    model_id="gpt-4.1-mini",
    temperature=0.2,
)
```

---

### 6. `create_agent`

#### Descrição

Cria um objeto `Agent` configurado com o modelo criado de acordo com o provedor e variante, incluindo parâmetros específicos para o modelo e para o agente.

#### Argumentos

- `provider` (str): Nome do provedor.
- `model_id` (Optional[str]): ID do modelo (opcional).
- `openai_variant` (str, keyword-only): Variante OpenAI, padrão `"chat"`.
- `model_kwargs` (Optional[Dict[str, Any]]): Dicionário de parâmetros para o modelo.
- `**agent_kwargs` (Any): Parâmetros extras encaminhados para o construtor do agente.

#### Retornos

- `Agent`: Instância da classe `Agent` configurada com o modelo e parâmetros fornecidos.

#### Raises

- Igual a `create_model` para a criação do modelo.

#### Exemplos

```python
agent = gateway.create_agent(
    provider="openai",
    openai_variant="chat",
    model_kwargs={"id": "gpt-4.1-mini", "temperature": 0.2},
    markdown=True,
)
```

---

### 7. `anthropic`

#### Descrição

Convenience method para criar modelo Anthropic Claude com parâmetros opcionais.

#### Argumentos

- `model_id` (Optional[str]): ID do modelo.
- `**kwargs` (Any): Parâmetros para o construtor do Claude.

#### Retornos

- `Claude`: Instância do modelo Claude.

#### Raises

- Igual a `create_model`.

#### Exemplos

```python
claude = gateway.anthropic(model_id="claude-v1", temperature=0.5)
```

---

### 8. `google`

#### Descrição

Convenience method para criar modelo Google Gemini com parâmetros opcionais.

#### Argumentos

- `model_id` (Optional[str]): ID do modelo.
- `**kwargs` (Any): Parâmetros para o construtor do Gemini.

#### Retornos

- `Gemini`: Instância do modelo Gemini.

#### Raises

- Igual a `create_model`.

#### Exemplos

```python
gemini = gateway.google(model_id="gemini-pro", max_tokens=1000)
```

---

### 9. `groq`

#### Descrição

Convenience method para criar modelo Groq com parâmetros opcionais.

#### Argumentos

- `model_id` (Optional[str]): ID do modelo.
- `**kwargs` (Any): Parâmetros para o construtor do Groq.

#### Retornos

- `Groq`: Instância do modelo Groq.

#### Raises

- Igual a `create_model`.

#### Exemplos

```python
groq_model = gateway.groq(model_id="groq-xyz")
```

---

### 10. `openai_chat`

#### Descrição

Convenience method para criar modelo OpenAIChat com parâmetros opcionais.

#### Argumentos

- `model_id` (Optional[str]): ID do modelo.
- `**kwargs` (Any): Parâmetros para o construtor do OpenAIChat.

#### Retornos

- `OpenAIChat`: Instância do modelo OpenAIChat.

#### Raises

- Igual a `create_model`.

#### Exemplos

```python
chat = gateway.openai_chat(model_id="gpt-4")
```

---

### 11. `openai_responses`

#### Descrição

Convenience method para criar modelo OpenAIResponses com parâmetros opcionais.

#### Argumentos

- `model_id` (Optional[str]): ID do modelo.
- `**kwargs` (Any): Parâmetros para o construtor do OpenAIResponses.

#### Retornos

- `OpenAIResponses`: Instância do modelo OpenAIResponses.

#### Raises

- Igual a `create_model`.

#### Exemplos

```python
responses = gateway.openai_responses(model_id="some-id")
```

---

### 12. `open_responses`

#### Descrição

Convenience method para criar modelo OpenResponses com parâmetros opcionais.

#### Argumentos

- `model_id` (Optional[str]): ID do modelo.
- `**kwargs` (Any): Parâmetros para o construtor do OpenResponses.

#### Retornos

- `OpenResponses`: Instância do modelo OpenResponses.

#### Raises

- Igual a `create_model`.

#### Exemplos

```python
open_resp = gateway.open_responses(model_id="openresp-1")
```

---

### 13. `openai_like`

#### Descrição

Convenience method para criar modelo OpenAILike com parâmetros opcionais.

#### Argumentos

- `model_id` (Optional[str]): ID do modelo.
- `**kwargs` (Any): Parâmetros para o construtor do OpenAILike.

#### Retornos

- `OpenAILike`: Instância do modelo OpenAILike.

#### Raises

- Igual a `create_model`.

#### Exemplos

```python
like_model = gateway.openai_like(model_id="like-1")
```

---

### 14. `_resolve_factory_key`

#### Descrição

Resolve a chave interna usada para acessar o construtor do modelo dado o nome do provedor e variante (se OpenAI).

#### Argumentos

- `provider` (str): Nome do provedor.
- `openai_variant` (str): Variante OpenAI. Padrão `"chat"`.

#### Retornos

- `str`: Chave do dicionário de fábricas para obter o construtor.

#### Raises

- `ValueError`: Se provedor ou variante forem inválidos.

#### Exemplos

```python
key = gateway._resolve_factory_key("openai", "like")
print(key)  # "openai.like"
```

---

### 15. `_get_constructor_param_names`

#### Descrição

Retorna nomes dos parâmetros do construtor da classe de modelo associada a uma chave de fábrica.

#### Argumentos

- `factory_key` (str): Chave do construtor do modelo.

#### Retornos

- `List[str]`: Lista de nomes dos parâmetros, exceto `self`.

#### Exemplos

```python
params = gateway._get_constructor_param_names("openai.chat")
print("temperature" in params)
```

---

### 16. `_validate_kwargs`

#### Descrição

Valida se as chaves do dicionário de parâmetros são válidas para o construtor do modelo.

#### Argumentos

- `factory_key` (str): Chave do construtor.
- `kwargs` (Dict[str, Any]): Parâmetros a validar.

#### Raises

- `ValueError`: Se encontrar parâmetros inválidos.

#### Exemplos

```python
gateway._validate_kwargs("openai.chat", {"temperature": 0.7, "foo": 123})
# Gera ValueError: parâmetro 'foo' inválido
```

---

# Exemplos Reais de Uso

```python
if __name__ == "__main__":
    gateway = ModelGateway(strict_validation=True)

    # Criando um modelo OpenAI Chat com ID e temperatura ajustada
    chat_model = gateway.create_model(
        provider="openai",
        openai_variant="chat",
        model_id="gpt-4.1-mini",
        temperature=0.2,
    )

    # Criando um agente com o mesmo modelo e opção markdown ativada
    agent = gateway.create_agent(
        provider="openai",
        openai_variant="chat",
        model_kwargs={"id": "gpt-4.1-mini", "temperature": 0.2},
        markdown=True,
    )

    _ = chat_model
    agent.print_response("Hello!")

    # python -m src.agents.utils.model_gateway
```

Essa documentação permite que desenvolvedores integrem rapidamente modelos de múltiplos provedores de forma segura, robusta e intuitiva usando a abstração poderosa oferecida pela classe `ModelGateway`.