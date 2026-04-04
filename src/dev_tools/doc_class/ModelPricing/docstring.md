```python
class ModelPricing:
    """
    Classe que representa o modelo de precificação para diferentes modelos de linguagem, permitindo calcular o custo com base no número de tokens de entrada e saída.

    Args: 
    :param model (str): O nome do modelo para o qual se deseja calcular os custos.    

    Methods:
            generate_post(topic): Explica o metodo em uma frase
    """

    COST_MODELS = {
        # Cost per million tokens in USD
        "gpt-4.1-mini": {"input": 0.4, "output": 1.6}
    }

    def __init__(self, model: str):
        if model not in self.COST_MODELS:
            raise ValueError(f"Modelo não suportado: {model}")
        self.model = model
        self.prices = self.COST_MODELS[model]

    def input_rate_per_token(self) -> float:
        """
        Retorna a taxa de custo por token para entradas, convertendo o custo por milhão de tokens para por token.

        Returns:
                float: O custo por token de entrada em dólares.
        """
        return self.prices["input"] / 1_000_000

    def output_rate_per_token(self) -> float:
        """
        Retorna a taxa de custo por token para saídas, convertendo o custo por milhão de tokens para por token.

        Returns:
                float: O custo por token de saída em dólares.
        """
        return self.prices["output"] / 1_000_000

if __name__ == "__main__":
    # Exemplo de uso
    model = "gpt-4.1-mini"
    input_token_count = 946
    output_token_count = 255
    total_token_count = 1201

    model_pricing = ModelPricing(model)
    input_cost = model_pricing.input_rate_per_token() * input_token_count
    output_cost = model_pricing.output_rate_per_token() * output_token_count

    print(f"\nCusto de entrada (USD): {input_cost:.6f}")
    print(f"Custo de saída (USD): {output_cost:.6f}\n")
```