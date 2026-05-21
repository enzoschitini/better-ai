import logging
from src.chat.utils.logging_utils import setup_logging

#setup_logging()

class CostCalculator:
    """Responsável por calcular e formatar custos de tokens, com logging."""

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
            logging.error(
                f"Modelo '{model_name}' não encontrado ao inicializar CostCalculator."
            )
            raise ValueError(f"Modelo '{model_name}' não encontrado.")

        self.model_name = model_name
        self.model_cost = self.COST_MODELS[model_name]

        logging.info(
            f"CostCalculator inicializado — modelo='{self.model_name}', custos={self.model_cost}"
        )

    def _format_decimal(self, value: float) -> str:
        return f"{value:.6f}"

    def calculate(self, tokens_response: dict) -> dict:
        try:
            logging.debug(
                f"Iniciando cálculo de custos no modelo '{self.model_name}' "
                f"com dados: {tokens_response}"
            )

            total_input = tokens_response["tokens_estimados"]["input"]["combined"]["tokens_estimated"]
            total_output = tokens_response["tokens_estimados"]["output"]["tokens_estimated"]

            logging.info(
                f"Tokens estimados — input={total_input}, output={total_output}, modelo='{self.model_name}'"
            )

            # Custo por milhão de tokens
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

            logging.info(
                f"Cálculo concluído com sucesso — modelo='{self.model_name}', "
                f"custo_total_usd={tokens_response['cost']['total_cost_usd']}"
            )

            return tokens_response

        except Exception as e:
            logging.error(
                f"Erro ao calcular custos no modelo '{self.model_name}': {str(e)}"
            )
            raise e





import pytest


def mock_tokens_response(input_tokens=1000, output_tokens=500):
    return {
        "tokens_estimados": {
            "input": {
                "combined": {
                    "tokens_estimated": input_tokens
                }
            },
            "output": {
                "tokens_estimated": output_tokens
            }
        }
    }


def test_cost_calculator_initialization_success():
    calculator = CostCalculator("gpt-4o-mini")

    assert calculator.model_name == "gpt-4o-mini"
    assert "input" in calculator.model_cost
    assert "output" in calculator.model_cost


def test_cost_calculator_invalid_model():
    with pytest.raises(ValueError):
        CostCalculator("modelo-inexistente")


def test_cost_calculator_calculate_success():
    import json
    calculator = CostCalculator("gpt-4o-mini")
    tokens_response = mock_tokens_response(1000, 500)

    result = calculator.calculate(tokens_response)

    assert "cost" in result

    cost = result["cost"]

    assert cost["modelo"] == "gpt-4o-mini"
    assert cost["input_tokens"] == 1000
    assert cost["output_tokens"] == 500
    assert cost["total_tokens"] == 1500

    # Custos esperados
    expected_input_cost = (1000 / 1_000_000) * 0.15
    expected_output_cost = (500 / 1_000_000) * 0.60
    expected_total_cost = expected_input_cost + expected_output_cost

    assert float(cost["input_cost_usd"]) == pytest.approx(expected_input_cost, rel=1e-6)
    assert float(cost["output_cost_usd"]) == pytest.approx(expected_output_cost, rel=1e-6)
    assert float(cost["total_cost_usd"]) == pytest.approx(expected_total_cost, rel=1e-6)

    print(json.dumps(result["cost"], indent=2))


def test_cost_calculator_invalid_tokens_payload():
    calculator = CostCalculator("gpt-4o-mini")

    invalid_payload = {
        "tokens_estimados": {
            "input": {}
        }
    }

    with pytest.raises(Exception):
        calculator.calculate(invalid_payload)

# python -m src.chat.tokens_calculator.cost_calculator