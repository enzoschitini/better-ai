import json
import tiktoken

class EmbeddingCostCalculator:
    # Por 1k tokens (1.000)
    MODEL_PRICES = {
        "text-embedding-3-small": 0.00002,
        "text-embedding-ada-002": 0.00010,
        "text-embedding-3-large": 0.00013

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

        return {
            "embedding_model": self.model,
            "model_cost_per_1000_tokens": self._format_cost(self.cost_per_1000),
            "characters": num_chars,
            "tokens": num_tokens,
            "cost_usd": self._format_cost(total_cost),
        }

    def calculate_cost_json(self, text: str) -> str:
        return json.dumps(self.calculate_cost(text), indent=4)



from src.chat.utils.mongo_manage import MongoDBManager
from datetime import datetime

mongo = MongoDBManager()

calc = EmbeddingCostCalculator("text-embedding-3-large")

texto = "Este é um texto de teste para embeddding."

resultado = calc.calculate_cost_json(texto)
print(resultado)

"""
mongo.salvar_payload(
    database_name="betterai_embeddings",
    collection_name="embedding_costs",
    payload={
        "rate": "dollar_rates",
        "dollar_rate_EUR": 0.85,
        "dollar_rate_BRL": 5.46,
    }
)

mongo.atualizar_documentos(
    database_name="betterai_embeddings",
    collection_name="embedding_costs",
    filtro={"rate": "dollar_rates"},
    novos_valores={"dollar_rate_BRL": 5.46})
"""


"""
calc = EmbeddingCostCalculator("text-embedding-3-large")

texto = "Este é um texto de teste para embeddding."

resultado = calc.calculate_cost_json(texto)
print(resultado)

{
    "model": "text-embedding-3-large",
    "characters": 41,
    "tokens": 12,
    "cost_usd": 0.000002
}

python -m src.embedding_reference.cost
"""