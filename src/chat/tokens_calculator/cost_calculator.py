class CostCalculator:
    """Responsável por calcular e formatar custos de tokens."""

    COST_MODELS = {
        "gpt-4o-mini": {"input": 0.15, "cached_input": 0.075, "output": 0.60},
        "gpt-4o": {"input": 2.50, "cached_input": 1.25, "output": 10.00},
        "gpt-3.5-turbo": {"input": 0.50, "cached_input": 0.25, "output": 1.50},
        "claude-3-haiku": {"input": 0.25, "cached_input": 0.125, "output": 1.25},
        "claude-3-sonnet": {"input": 3.00, "cached_input": 1.50, "output": 15.00},
        "claude-3-opus": {"input": 15.00, "cached_input": 7.50, "output": 75.00},
        "llama3-8b": {"input": 0.05, "cached_input": 0.025, "output": 0.08},
        "mixtral-8x7b": {"input": 0.20, "cached_input": 0.10, "output": 0.30},
    }

    def __init__(self, model_name: str):
        if model_name not in self.COST_MODELS:
            raise ValueError(f"Modelo '{model_name}' não encontrado.")
        self.model_name = model_name
        self.model_cost = self.COST_MODELS[model_name]

    def _format_decimal(self, value: float) -> str:
        return f"{value:.6f}"

    def calculate(self, tokens_response: dict) -> dict:
        total_input = tokens_response["tokens_estimados"]["input"]["combined"]["tokens_estimated"]
        total_output = tokens_response["tokens_estimados"]["output"]["tokens_estimated"]

        cost_input = (total_input / 1_000_000) * self.model_cost["input"]
        cost_output = (total_output / 1_000_000) * self.model_cost["output"]
        cost_total = cost_input + cost_output

        tokens_response["cost"] = {
            "modelo": self.model_name,
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "input_cost_usd": self._format_decimal(cost_input),
            "output_cost_usd": self._format_decimal(cost_output),
            "total_cost_usd": self._format_decimal(cost_total),
        }
        return tokens_response
