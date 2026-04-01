import tiktoken

class TokenCounter:
    def __init__(self, model: str):
        try:
            self.encoder = tiktoken.encoding_for_model(model)
        except KeyError:
            self.encoder = tiktoken.get_encoding("cl100k_base")

    def count(self, text: str) -> int:
        return len(self.encoder.encode(text)) if text else 0

class ModelPricing:
    COST_MODELS = {
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
    MODEL = "gpt-4.1-mini"
    INPUT_TEXT = "Olá, como posso ajudar você hoje?"
    OUTPUT_TEXT = "Olá! Estou aqui para ajudar. O que você gostaria de saber?"
    INPUT_TOKENS = 946
    OUTPUT_TOKENS = 255
    TOTAL_TOKENS = 1201

    # Test TokenCounter
    token_counter = TokenCounter(MODEL)
    input_token_count = token_counter.count(INPUT_TEXT)
    output_token_count = token_counter.count(OUTPUT_TEXT)

    print(f"\nTokens de entrada: {input_token_count}")
    print(f"Tokens de saída: {output_token_count}")

    # Test ModelPricing
    model_pricing = ModelPricing(MODEL)
    input_cost = model_pricing.input_rate_per_token() * input_token_count
    output_cost = model_pricing.output_rate_per_token() * output_token_count

    print(f"\nCusto de entrada (USD): {input_cost:.6f}")
    print(f"Custo de saída (USD): {output_cost:.6f}")


