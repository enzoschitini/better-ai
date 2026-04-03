import json
from typing import Optional
from fastapi import HTTPException
from io import BytesIO

from src.embedding.services.file_content_extractor import FileContentExtractor
from src.text_parse.content_parsing_agent import ContentParsingAgent
from src.tokens_calculate.module import ModelPricing, ExchangeRateService


default_config = {
    "model_provider": "OpenAI",
    "model_id": "gpt-4.1-mini",
    "debug_mode": True,
    "instructions": "Extraia dados do texto",
    "description": (
        "Leia o texto e extraia as informações relevantes conforme o esquema definido. "
        "Retorne um JSON estruturado com os dados extraídos. "
        "Caso não encontre alguma informação, retorne null para aquele campo."
    ),
}

class SimpleFileParse:
    def __init__(
        self,
        schema: str,
        file_bytes: BytesIO,
        file_extension: str,
        config: Optional[str] = None,
    ):
        self.schema = schema
        self.config = config
        self.file_bytes = file_bytes
        self.file_extension = file_extension
    
    def set_data(self):
        # Set metadata
        try:
            self.schema_data = json.loads(self.schema)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in schema")

        if self.config:
            try:
                config_input = json.loads(self.config)
                self.config_data = {**default_config, **config_input}
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON in config")
        else:
            self.config_data = default_config
    
    def extract_file_content(self):
        # Extract file content
        extractor = FileContentExtractor(
            file_bytes=self.file_bytes,
            file_extension=self.file_extension
        )
        self.result_extract = extractor.extract()
    
    def content_parsing(self):
        # Parse content with agent
        agent_parser = ContentParsingAgent(
            input_data={
                "file_content": self.result_extract["response"]
            },
            output_data=self.schema_data,
            config_data=self.config_data
        )

        content_parsed = agent_parser.run_agent()
        return agent_parser.format_response(content_parsed)

    def run(self):
        self.set_data()
        self.extract_file_content()
        response = self.content_parsing()

        # Calculate tokens and cost
        # Formatte response result + process
        # Save processed result in database

        return response

if __name__ == "__main__":
    # Exemplo de uso
    schema = """
    {
      "summary": {
        "type": "str",
        "description": "Resumo do conteúdo do arquivo"
      }
    }
    """
    config = """
    {
      "model_provider": "OpenAI",
      "model_id": "gpt-4.1-mini",
      "debug_mode": true,
      "instructions": "Extraia dados do texto",
      "description": "Leia o texto e extraia as informações relevantes conforme o esquema definido. Retorne um JSON estruturado com os dados extraídos. Caso não encontre alguma informação, retorne null para aquele campo."
    }
    """

    with open("src\\text_parse\\module\\Endurance.pdf", "rb") as f:
        file_bytes = BytesIO(f.read())

    parser = SimpleFileParse(
        schema=schema,
        config=config,
        file_bytes=file_bytes,
        file_extension="pdf"
    )

    response = parser.run()
    metadata = response.get("metadata", {})

    model_pricing = ModelPricing(metadata.get("model").get("id"))
    input_cost = model_pricing.input_rate_per_token() * metadata.get("tokens").get("input_tokens", 0)
    output_cost = model_pricing.output_rate_per_token() * metadata.get("tokens").get("output_tokens", 0)

    service = ExchangeRateService()
    rate = service.get_usd_rate()
    print(f"Cotação do dólar: {rate}")

    formatted_metadata = {
        "model": metadata.get("model"),
        "tokens": metadata.get("tokens"),
        "cost": {
            "input_cost_usd": input_cost,
            "output_cost_usd": output_cost,
            "total_cost_usd": input_cost + output_cost,
            "total_cost_brl": (input_cost + output_cost) * rate
        },
        "duration_s": metadata.get("duration_s"),
    }

    response = {
        "content": response.get("content"),
        "metadata": formatted_metadata
    }

    print("\nResposta do parser:")
    print(json.dumps(response, indent=2))

# python -m src.text_parse.module.simple_file_parse