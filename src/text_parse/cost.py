



schema = [
  {
    "name": "titolo",
    "type": "str",
    "title": "Títolo da notícia",
    "description": "Títolo principal da notícia",
    "examples": [
      "Governo anuncia novas medidas econômicas",
      "Descoberta científica revoluciona tratamento de doenças"
    ]
  },
  {
    "name": "descricao",
    "type": "str",
    "title": "Descrição da notícia",
    "description": "Resumo breve do conteúdo da notícia",
    "examples": [
      "O governo implementou uma série de medidas para estimular a economia nacional.",
      "Cientistas desenvolveram uma nova técnica que promete melhorar significativamente o tratamento de várias doenças."
    ]
  },
  {
    "name": "informacoes_chave",
    "type": "list",
    "title": "Informações chave",
    "description": "Lista de pontos importantes abordados na notícia",
    "items": {
      "type": "str"
    },
    "examples": [
      "Medidas incluem redução de impostos e incentivos para pequenas empresas.",
      "Nova técnica utiliza nanotecnologia para direcionar medicamentos diretamente às células afetadas."
    ]
  }
]


result = {
    "titolo": "Governo anuncia novas medidas econômicas",
    "descricao": "O governo implementou uma série de medidas para estimular a economia nacional.",
    "informacoes_chave": [
        "Medidas incluem redução de impostos e incentivos para pequenas empresas.",
        "Foco em inovação tecnológica e sustentabilidade."
    ]
}

scraper = """
O governo implementou uma série de medidas para estimular a economia nacional.O governo implementou uma série de medidas para estimular a economia nacional.O governo implementou uma série de medidas para estimular a economia nacional.
O governo implementou uma série de medidas para estimular a economia nacional.O governo implementou uma série de medidas para estimular a economia nacional.O governo implementou uma série de medidas para estimular a economia nacional.
O governo implementou uma série de medidas para estimular a economia nacional.O governo implementou uma série de medidas para estimular a economia nacional.O governo implementou uma série de medidas para estimular a economia nacional.
"""


import tiktoken
from src.embedding.tokens_calculator.dollar_rates import DollarRateService


class TokenCounter:
    """Responsável APENAS por contar tokens."""

    def __init__(self, model: str):
        try:
            self.encoder = tiktoken.encoding_for_model(model)
        except KeyError:
            self.encoder = tiktoken.get_encoding("cl100k_base")

    def count(self, text: str) -> int:
        return len(self.encoder.encode(text)) if text else 0


class ModelPricing:
    """Responsável APENAS por preços do modelo."""

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

    def __init__(self, model: str):
        if model not in self.COST_MODELS:
            raise ValueError(f"Modelo não suportado: {model}")
        self.model = model
        self.prices = self.COST_MODELS[model]

    def input_rate_usd(self) -> float:
        return self.prices["input"] / 1000

    def output_rate_usd(self) -> float:
        return self.prices["output"] / 1000


class CurrencyConverter:
    """Responsável APENAS por conversão de moedas."""

    def __init__(self):
        service = DollarRateService()
        self.rates = {
            "EUR": service.get_rate("EUR"),
            "BRL": service.get_rate("BRL"),
        }

    def convert(self, usd_value: float) -> dict:
        return {
            "eur": usd_value * self.rates["EUR"],
            "brl": usd_value * self.rates["BRL"],
        }


class LLMCostCalculator:
    """Responsável APENAS por orquestrar o cálculo."""

    def __init__(self, model: str):
        self.model = model
        self.token_counter = TokenCounter(model)
        self.pricing = ModelPricing(model)
        self.converter = CurrencyConverter()

    def calculate(self, input_text: str, output_text: str) -> dict:
        input_tokens = self.token_counter.count(input_text)
        output_tokens = self.token_counter.count(output_text)

        input_cost_usd = input_tokens * self.pricing.input_rate_usd()
        output_cost_usd = output_tokens * self.pricing.output_rate_usd()
        total_cost_usd = input_cost_usd + output_cost_usd

        input_conv = self.converter.convert(input_cost_usd)
        output_conv = self.converter.convert(output_cost_usd)
        total_conv = self.converter.convert(total_cost_usd)

        return {
            "llm_model": {
                "name": self.model,
                "input_cost_1k_usd": self.pricing.input_rate_usd(),
                "output_cost_1k_usd": self.pricing.output_rate_usd(),
            },
            "tokens": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            },
            "cost": {
                "usd": {
                    "input_cost_usd": f"{input_cost_usd:.6f}",
                    "output_cost_usd": f"{output_cost_usd:.6f}",
                    "total_cost_usd": f"{total_cost_usd:.6f}",
                },
                "eur": {
                    "input_cost_eur": f"{input_conv['eur']:.6f}",
                    "output_cost_eur": f"{output_conv['eur']:.6f}",
                    "total_cost_eur": f"{total_conv['eur']:.6f}",
                },
                "brl": {
                    "input_cost_brl": f"{input_conv['brl']:.6f}",
                    "output_cost_brl": f"{output_conv['brl']:.6f}",
                    "total_cost_brl": f"{total_conv['brl']:.6f}",
                },
            },
            "rates": self.converter.rates,
        }


def test(model: str, schema: dict, scraper: str, result: dict):
    import json

    input = str(schema) + str(scraper)
    output = str(result)

    calculator = LLMCostCalculator(model=model)

    cost_informations = calculator.calculate(
        input_text=input,
        output_text=output
    )

    print(json.dumps(cost_informations, indent=4, ensure_ascii=False))

"""
test(
    model="gpt-4o-mini",
    schema=schema,
    scraper=scraper,
    result=result
)
"""
# python -m src.text_parse.cost