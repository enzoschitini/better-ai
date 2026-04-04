# Classe `TokenCounter`

## Visão Geral

A classe `TokenCounter` tem como objetivo principal calcular a quantidade de tokens presentes em um texto, utilizando codificadores baseados nos modelos de linguagem da OpenAI. Isso é especialmente útil para quem trabalha com APIs que possuem limites baseados na quantidade de tokens, como GPT-3 e GPT-4, permitindo gerenciar melhor o custo e o tamanho das requisições.

Ela resolve o problema de precisar de uma contagem precisa de tokens para inputs de texto, algo crucial para limitações e otimizações em aplicações de NLP que dependem de modelos OpenAI. Na prática, você pode usar essa classe para, por exemplo, verificar se um texto está dentro do limite máximo de tokens permitido pelo modelo antes de enviar uma requisição.

## Fluxo de Execução

1. Instancie a classe `TokenCounter`, passando o nome do modelo que deseja usar para a codificação dos tokens (ex.: `"gpt-3.5-turbo"`). Isso define o padrão de tokenização adequado ao modelo.
2. Caso o nome do modelo não seja reconhecido, a classe automaticamente usa uma codificação base padrão (`cl100k_base`).
3. Chame o método `count`, passando o texto que quer contar.
4. O método retorna um número inteiro que representa a quantidade de tokens no texto.

## Tabela de Métodos da Classe

| Método  | Descrição                              |
|---------|-------------------------------------|
| `__init__` | Inicializa o codificador para o modelo desejado |
| `count` | Conta a quantidade de tokens em um texto |

## Variáveis de Ambiente

Não há variáveis de ambiente utilizadas pela classe.

## Pontos Importantes da Arquitetura e Insights

- A classe utiliza a biblioteca `tiktoken`, que é específica para tokenização de modelos da OpenAI, garantindo alta compatibilidade e precisão.
- A escolha da codificação é dinâmica, baseada no nome do modelo informado. Caso o modelo não seja conhecido, um padrão seguro é usado para evitar erros.
- Encapsula o funcionamento interno do codificador, oferecendo uma interface simples para contar tokens, facilitando a integração em projetos maiores.
- A classe não depende de outras classes além do módulo externo `tiktoken`.
- Seu design é minimalista, focado em um único propósito, seguindo o princípio de responsabilidade única.

# Descrição da Classe e Métodos

## Classe `TokenCounter`

### Descrição

Classe responsável por contar a quantidade de tokens em textos, utilizando codificadores da biblioteca `tiktoken`, que reproduzem como os modelos da OpenAI interpretam e segmentam palavras em tokens.

### Argumentos do Construtor

| Argumento | Tipo | Descrição | Valor Padrão |
|-----------|------|-----------|--------------|
| model     | str  | Nome do modelo OpenAI para definir a codificação dos tokens (ex.: `"gpt-3.5-turbo"`). | Nenhum |

### Métodos

---

### 1. `__init__`

### Descrição

Inicializa um codificador de tokens baseado no modelo especificado. Se o modelo não for reconhecido, usa uma codificação padrão.

### Argumentos

- model (str): nome do modelo para definir a codificação

### Retornos

- Não retorna valor.

### Raises

- Nenhum explicitamente, mas ignora `KeyError` ao buscar o codificador para o modelo.

### Exemplos

```python
counter = TokenCounter("gpt-3.5-turbo")
```

---

### 2. `count`

### Descrição

Conta quantos tokens o texto fornecido possui, convertendo o texto usando o codificador associado ao modelo.

### Argumentos

- text (str): Texto cuja quantidade de tokens será computada.

### Retornos

- int: número total de tokens encontrados no texto. Retorna 0 se o texto for vazio ou `None`.

### Raises

- Nenhum.

### Exemplos

```python
counter = TokenCounter("gpt-3.5-turbo")
num_tokens = counter.count("Hello, how are you?")
print(num_tokens)  # Saída provável: 6
```

Este exemplo mostra a contagem aproximada de tokens para a frase "Hello, how are you?", que em geral possui 6 tokens segundo a tokenização do modelo indicado.