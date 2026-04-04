# Classe `ModelPricing`

## Visão Geral

A classe `ModelPricing` foi criada para representar um modelo de precificação de linguagens naturais baseadas em tokens, permitindo calcular o custo associado ao processamento de entradas e saídas em diferentes modelos de linguagem. Ela resolve o problema de precificar o uso de modelos de linguagem, convertendo custos por milhão de tokens para custos unitários, facilitando a estimativa financeira para chamadas a APIs ou uso de modelos.

Na prática, essa classe pode ser usada para obter o custo de uma requisição que envolva uma certa quantidade de tokens de entrada e saída de forma rápida e direta, bastando informar o modelo desejado. Isso é útil para quem trabalha com APIs de processamento de linguagem, permitindo estimar gastos e controlar o uso baseado em tokens.

## Fluxo de Execução

1. Inicializa-se uma instância da classe `ModelPricing` passando o nome do modelo como parâmetro. Caso o modelo não seja suportado, uma exceção é lançada.
2. Através dos métodos `input_rate_per_token` e `output_rate_per_token`, obtém-se o custo unitário por token de entrada e saída, respectivamente, convertendo os valores que são originalmente definidos por milhão de tokens.
3. Multiplicam-se esses valores pelo número real de tokens processados para calcular o custo total de entrada e saída.
4. O resultado final é o custo estimado em dólares para o uso do modelo referente à quantidade de tokens informada.

## Tabela de Métodos da Classe

| Método               | Descrição                                 |
|----------------------|-------------------------------------------|
| `__init__`           | Inicializa o objeto com o modelo escolhido, validando-o. |
| `input_rate_per_token`| Retorna o custo unitário por token de entrada. |
| `output_rate_per_token`| Retorna o custo unitário por token de saída. |

## Pontos Importantes da Arquitetura e Insights

- A precificação é armazenada em `COST_MODELS`, um dicionário que associa o nome do modelo aos custos por milhão de tokens para entrada e saída.
- O método de cálculo converte o custo por milhão para custo por token dividindo o valor por 1.000.000, garantindo flexibilidade para diferentes escalas.
- Essa abordagem encapsula a precificação em uma classe, facilitando a manutenção e extensão para novos modelos, bastando adicionar entradas no dicionário.
- Ao validar o modelo na inicialização, evita-se erros posteriores durante o cálculo, garantindo segurança na utilização da classe.

# Descrição da Classe e Métodos

## Classe `ModelPricing`

### Descrição

Classe para cálculo do custo de uso de modelos de linguagem, baseado na quantidade de tokens de entrada e saída e nos preços definidos por modelo. Proporciona uma interface simples para converter preços por milhão de tokens em preços unitários.

### Argumentos do Construtor

| Argumento | Tipo  | Descrição                                | Valor Padrão |
|-----------|-------|-----------------------------------------|--------------|
| model     | str   | O nome do modelo para o qual calcular os custos. | Nenhum       |

### Métodos

---

### 1. `__init__`

### Descrição

Inicializa a instância da classe verificando se o modelo informado existe na base de preços suportados, e atribui os preços correspondentes.

### Argumentos

- model (str): nome do modelo de linguagem utilizado para consultar os preços.

### Retornos

- Não retorna valor.

### Raises

- ValueError: Se o modelo informado não estiver listado nos modelos suportados.

### Exemplos

```python
model_pricing = ModelPricing("gpt-4.1-mini")
```

---

### 2. `input_rate_per_token`

### Descrição

Calcula e retorna o custo por token de entrada (input), baseado no preço por milhão de tokens configurado.

### Argumentos

- Nenhum.

### Retornos

- float: custo em dólares por token de entrada.

### Raises

- Nenhum.

### Exemplos

```python
input_cost_per_token = model_pricing.input_rate_per_token()
# Retorna algo como 0.0000004 para "gpt-4.1-mini"
```

---

### 3. `output_rate_per_token`

### Descrição

Calcula e retorna o custo por token de saída (output), baseado no preço por milhão de tokens configurado.

### Argumentos

- Nenhum.

### Retornos

- float: custo em dólares por token de saída.

### Raises

- Nenhum.

### Exemplos

```python
output_cost_per_token = model_pricing.output_rate_per_token()
# Retorna algo como 0.0000016 para "gpt-4.1-mini"
```

---

## Exemplo Completo de Uso

```python
model = "gpt-4.1-mini"
input_token_count = 946
output_token_count = 255

model_pricing = ModelPricing(model)
input_cost = model_pricing.input_rate_per_token() * input_token_count
output_cost = model_pricing.output_rate_per_token() * output_token_count

print(f"Custo de entrada (USD): {input_cost:.6f}")
print(f"Custo de saída (USD): {output_cost:.6f}")
```

Saída esperada:

```
Custo de entrada (USD): 0.000378
Custo de saída (USD): 0.000408
```

Este exemplo ilustra como calcular o custo total com base em contagens de tokens reais para um modelo específico, facilitando controle financeiro e análise de custos para chamadas a modelos de linguagem.