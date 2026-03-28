# Documentação Didática da Classe `CostCalculator`

## Visão Geral

A classe `CostCalculator` é responsável por calcular custos relacionados ao consumo de tokens de modelos de linguagem e à geração de imagens, utilizando uma tabela de preços específica. Ela resolve o problema de atribuir custos financeiros precisos para diferentes tipos de consumo em sistemas que utilizam modelos baseados em tokens, como APIs de processamento de linguagem natural e geração de imagens automatizadas.

Na prática, a classe pode ser usada em sistemas que precisam calcular custos detalhados de uso de APIs pagas, especialmente em contextos que envolvem geração de texto e imagens. Permite combinar informações de custo parciais e obter um custo total considerando fatores como tokens gerados, imagens criadas e até uso de cache para otimização.

---

## Fluxo de Execução

1. **Inicialização:** Instancie a classe `CostCalculator`, passando opcionalmente uma instância ou classe de tabela de preços (por padrão, usa `PricingTable`).
2. **Mesclar informações de custo** (opcional): Caso tenha múltiplas informações de custo parciais, use o método `merge_cost_information` para somá-las e consolidar em um único dicionário.
3. **Calcular custo total:** Chame o método `calculate`, fornecendo o modelo utilizado, a quantidade de tokens no prompt e saída, total de tokens, e o número de imagens geradas, além de possíveis dados de cache.
4. **Receber resultado:** O método `calculate` retorna um dicionário com o custo detalhado para cada componente (tokens de prompt, tokens de saída, imagens, cache) e o custo total em dólares, já arredondado.

---

## Tabela de Métodos da Classe

| Método                  | Descrição                                                      |
|-------------------------|----------------------------------------------------------------|
| `__init__`              | Inicializa o calculador de custos com uma tabela de preços.     |
| `merge_cost_information`| Combina múltiplos dicionários de custo em um só, somando tokens.|
| `calculate`             | Calcula o custo total usando dados de tokens, imagens e cache.  |

---

## Pontos Importantes da Arquitetura e Insights

- **Design modular**: O cálculo de custos é desacoplado da tabela de preços, que é passada como dependência, facilitando a extensão para diferentes esquemas de preços.
- **Tratamento de cache**: A classe inclui cálculos separados para custos relacionados a tokens armazenados e uso de cache, o que é um diferencial para cenários que utilizam armazenamento temporário para otimizar chamadas externas.
- **Validação explícita**: No método `merge_cost_information`, existe verificação para garantir que pelo menos dois conjuntos de dados sejam fornecidos, reforçando a segurança do uso.
- **Padronização de custo por milhão de tokens**: Os cálculos são sempre baseados em custo por milhão de tokens, facilitando a compreensão e escalabilidade dos custos.
- **Uso de tipos**: A tipagem das variáveis está clara, incluindo valores padrão para parâmetros opcionais, o que melhora a legibilidade e a integração em sistemas tipados.
- A classe utiliza a classe `PricingTable` para obter os preços, integrando-se ao sistema de preços externo.

---

# Descrição da Classe e Métodos

## Classe `CostCalculator`

### Descrição

Classe que calcula os custos financeiros de uso de modelos de linguagem e geração de imagens com base na quantidade de tokens consumidos, imagens produzidas e utilização de cache, utilizando uma tabela de preços para conversão.

### Argumentos do Construtor

| Argumento      | Tipo          | Descrição                                      | Valor Padrão    |
|----------------|---------------|------------------------------------------------|-----------------|
| pricing_table  | `PricingTable`| Tabela de preços que define os valores monetários para tokens e imagens.| `PricingTable` |

---

### 1. `__init__`

### Descrição

Método construtor que inicializa o objeto com uma tabela de preços para cálculo dos custos.

### Argumentos

- `pricing_table` (PricingTable): A tabela de preços utilizada para efetuar os cálculos dos valores.

### Retornos

- Não retorna valor.

### Raises

- Nenhum.

### Exemplos

```python
calculator = CostCalculator()
# Ou com uma tabela de preços personalizada
calculator_custom = CostCalculator(custom_pricing_table)
```

---

### 2. `merge_cost_information`

### Descrição

Combina vários dicionários com informações de custo agregando as quantidades de tokens (prompt, output e total) em um único dicionário consolidado.

### Argumentos

- `cost_infos` (List[Dict]): Lista de dicionários, cada um representando informações de custo parcial.

### Retornos

- `Dict`: Dicionário único com as somas totais de `"prompt_tokens"`, `"output_tokens"` e `"total_tokens"`.

### Raises

- `ValueError`: Se a lista `cost_infos` não possuir pelo menos dois elementos.

### Exemplos

```python
cost1 = {"prompt_tokens": 1200, "output_tokens": 800, "total_tokens": 2000}
cost2 = {"prompt_tokens": 500, "output_tokens": 300, "total_tokens": 800}

merged = calculator.merge_cost_information([cost1, cost2])
print(merged)
# Saída:
# {'prompt_tokens': 1700, 'output_tokens': 1100, 'total_tokens': 2800}
```

---

### 3. `calculate`

### Descrição

Calcula os custos em dólares baseando-se nas quantidades de tokens de prompt, saída, total, número de imagens geradas, e custos associados a caching, aplicando os preços definidos na tabela.

### Argumentos

- `model` (str): Nome do modelo para buscar o preço correspondente.
- `prompt_tokens` (int): Quantidade de tokens usados no prompt.
- `output_tokens` (int): Quantidade de tokens gerados na saída.
- `total_tokens` (int): Total de tokens processados.
- `num_images` (int, opcional): Número de imagens geradas. Default é 0.
- `cached_prompt_tokens` (int, opcional): Tokens de prompt armazenados em cache. Default é 0.
- `cache_storage_tokens` (int, opcional): Tokens armazenados para custeio em cache. Default é 0.
- `cache_storage_hours` (float, opcional): Horas de armazenamento em cache. Default é 0.0.

### Retornos

- `Dict[str, float]`: Dicionário contendo as quantidades de tokens e os custos em dólares (`prompt_usd`, `output_usd`, `images_usd`) e o custo total (`total_usd`), com valores arredondados a 6 casas decimais.

### Raises

- Nenhum explícito (assumindo que o método `get` da tabela de preços retorna preços válidos).

### Exemplos

```python
result = calculator.calculate(
    model="gpt-4",
    prompt_tokens=1500,
    output_tokens=1000,
    total_tokens=2500,
    num_images=2,
    cached_prompt_tokens=500,
    cache_storage_tokens=2000,
    cache_storage_hours=5.0
)

print(result)
# Exemplo de saída (valores ilustrativos):
# {
#   'prompt_tokens': 1500,
#   'output_tokens': 1000,
#   'total_tokens': 2500,
#   'prompt_usd': 0.00075,
#   'output_usd': 0.00050,
#   'images_usd': 0.012,
#   'total_usd': 0.01325
# }
```

---

Com essa documentação, desenvolvedores podem compreender claramente os propósitos, funcionamento e como integrar/utilizar a classe `CostCalculator` em seus projetos para gerenciamento eficiente dos custos de uso de APIs baseadas em tokens e geração de imagens.