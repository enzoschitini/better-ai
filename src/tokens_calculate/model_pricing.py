class ModelPricing:
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
        return self.prices["input"] / 1_000_000

    def output_rate_per_token(self) -> float:
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
