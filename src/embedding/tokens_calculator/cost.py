import json
import tiktoken
from src.embedding.tokens_calculator.dollar_rates import DollarRateService

class EmbeddingCostCalculator:
    # Por 1k tokens (1.000)
    MODEL_PRICES = {
        "text-embedding-3-small": 0.020,
        "text-embedding-ada-002": 0.10,
        "text-embedding-3-large": 0.13

    }

    def __init__(self, model_name: str = "text-embedding-3-large"):
        if model_name not in self.MODEL_PRICES:
            raise ValueError(f"Modelo '{model_name}' não encontrado.")
        
        self.model = model_name
        self.cost_per_1000 = self.MODEL_PRICES[model_name]
        self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))

    def _format_cost(self, value: float) -> str:
        formatted = f"{value:.10f}".rstrip("0")
        if formatted.endswith("."):
            formatted = formatted[:-1]
        return formatted

    def calculate_cost(self, text: str) -> dict:
        num_chars = len(text)
        num_tokens = self.count_tokens(text)
        total_cost = (num_tokens / 1000) * self.cost_per_1000

        service = DollarRateService()
        dollar_rates = {
            "EUR": service.get_rate("EUR"),
            "BRL": service.get_rate("BRL")
        }

        cost_usd = float(self._format_cost(total_cost))

        cost_eur = cost_usd * dollar_rates["EUR"]
        cost_brl = cost_usd * dollar_rates["BRL"]

        cost_payload = {
            "embedding_model": self.model,
            "model_cost_per_1000_tokens": self._format_cost(self.cost_per_1000),
            "characters": num_chars,
            "tokens": num_tokens,
            "total_cost": {
                "cost_usd": self._format_cost(cost_usd),
                "cost_eur": self._format_cost(cost_eur),
                "cost_brl": self._format_cost(cost_brl)
            },
            "dollar_rates": dollar_rates
        }

        return cost_payload

    def calculate_cost_json(self, text: str) -> str:
        return self.calculate_cost(text)



"""
python -m src.embedding_reference.cost

calc = EmbeddingCostCalculator("text-embedding-3-large")

texto = "Este é um texto de teste para embeddding."

resultado = calc.calculate_cost_json(texto)
print(resultado)
"""
