from abc import ABC, abstractmethod


class BasePricing(ABC):
    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    def cost(self, tokens: int) -> float:
        pass


# ========================
# CHAT MODELS
# ========================
class ChatModelPricing(BasePricing):

    COST_MODELS = {
        # Cost per million tokens in USD
        "gpt-4.1-mini": {"input": 0.4, "output": 1.6}
    }

    def __init__(self, model: str):
        if model not in self.COST_MODELS:
            raise ValueError(f"Modelo de chat não suportado: {model}")
        super().__init__(model)
        self.prices = self.COST_MODELS[model]

    def input_cost(self, tokens: int) -> float:
        return (self.prices["input"] / 1_000_000) * tokens

    def output_cost(self, tokens: int) -> float:
        return (self.prices["output"] / 1_000_000) * tokens

    def total_cost(self, input_tokens: int, output_tokens: int) -> float:
        return self.input_cost(input_tokens) + self.output_cost(output_tokens)

    def cost(self, tokens: int) -> float:
        raise NotImplementedError("Use input_cost/output_cost para chat models")


# ========================
# EMBEDDING MODELS
# ========================
class EmbeddingModelPricing(BasePricing):

    COST_MODELS = {
        "text-embedding-3-small": 0.020,
        "text-embedding-ada-002": 0.10,
        "text-embedding-3-large": 0.13
    }

    def __init__(self, model: str):
        if model not in self.COST_MODELS:
            raise ValueError(f"Modelo de embedding não suportado: {model}")
        super().__init__(model)
        self.price_per_million = self.COST_MODELS[model]

    def cost(self, tokens: int) -> float:
        return (self.price_per_million / 1_000_000) * tokens


# ========================
# FACTORY
# ========================
class ModelPricingFactory:

    @staticmethod
    def create(model: str) -> BasePricing:
        if model in ChatModelPricing.COST_MODELS:
            return ChatModelPricing(model)

        if model in EmbeddingModelPricing.COST_MODELS:
            return EmbeddingModelPricing(model)

        raise ValueError(f"Modelo não suportado: {model}")

if __name__ == "__main__":
    # Embedding
    model = "text-embedding-3-large"
    pricing = ModelPricingFactory.create(model)

    tokens = 5000
    cost = pricing.cost(tokens)

    print(f"Custo embedding: ${cost:.6}")

    # Chat
    model = "gpt-4.1-mini"
    pricing = ModelPricingFactory.create(model)

    input_tokens = 3000
    output_tokens = 1000

    input_cost = pricing.input_cost(input_tokens)
    output_cost = pricing.output_cost(output_tokens)

    cost = pricing.total_cost(input_tokens, output_tokens)

    print(f"Custo input: ${input_cost:.6}")
    print(f"Custo output: ${output_cost:.6}")
    print(f"Custo total: ${cost:.6}")

"""
Aggiustare src.tokens_calculate.module
"""