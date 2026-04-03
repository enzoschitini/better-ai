import json
from typing import Optional
from fastapi import HTTPException
from io import BytesIO

from src.text_parse.content_parsing_agent import ContentParsingAgent
from src.text_parse.config import DocumentParseConfig
from src.embedding.services.file_content_extractor import FileContentExtractor
from src.tokens_calculate.module import ModelPricing, ExchangeRateService
from src.database.no_relational_db.router import DocumentStore


class DocumentParse:
    def __init__(
        self,
        job_id: str,
        metadata: dict,
        schema: str,
        file_bytes: BytesIO,
        file_extension: str,
        config: Optional[str] = None,
    ):
        self.job_id = job_id
        self.metadata = metadata
        self.schema = schema
        self.config = config
        self.file_bytes = file_bytes
        self.file_extension = file_extension

        system_settings = DocumentParseConfig()
        self.default_config = system_settings.default_config
        self.database_name = system_settings.database_name
        self.collection_name = system_settings.collection_name

    def run(self):
        self._load_schema_and_config()
        self._extract_file_content()
        self._parse_content()
        self._calculate_costs()
        self._build_response()
        self._save()

        return self.response

    def _load_schema_and_config(self):
        # Set metadata
        try:
            self.schema_data = json.loads(self.schema)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in schema")

        if self.config:
            try:
                config_input = json.loads(self.config)
                self.config_data = {**self.default_config, **config_input}
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON in config")
        else:
            self.config_data = self.default_config
    
    def _extract_file_content(self):
        # Extract file content
        extractor = FileContentExtractor(
            file_bytes=self.file_bytes,
            file_extension=self.file_extension
        )
        self.result_extract = extractor.extract()
    
    def _parse_content(self):
        # Parse content with agent
        agent_parser = ContentParsingAgent(
            input_data={
                "file_content": self.result_extract["response"]
            },
            output_data=self.schema_data,
            config_data=self.config_data
        )

        raw_content_parsed = agent_parser.run_agent()
        self.agent_response = agent_parser.format_response(raw_content_parsed)
    
    def _calculate_costs(self):
        # Calculate tokens and cost
        self.info_process = self.agent_response.get("metadata", {})

        model_pricing = ModelPricing(self.info_process.get("model").get("id"))
        self.input_cost = model_pricing.input_rate_per_token() * self.info_process.get("tokens").get("input_tokens", 0)
        self.output_cost = model_pricing.output_rate_per_token() * self.info_process.get("tokens").get("output_tokens", 0)

        service = ExchangeRateService()
        self.rate = service.get_usd_rate()
    
    def _build_response(self):
        # Formatte response result + process
        formatted_info_process = {
            "model": self.info_process.get("model"),
            "tokens": self.info_process.get("tokens"),
            "cost": {
                "input_cost_usd": self.input_cost,
                "output_cost_usd": self.output_cost,
                "total_cost_usd": self.input_cost + self.output_cost,
                "total_cost_brl": (self.input_cost + self.output_cost) * self.rate
            },
            "duration_s": self.info_process.get("duration_s"),
        }

        self.response = {
            "job_id": self.job_id,
            "metadata": self.metadata,
            "content": self.agent_response.get("content"),
            "process_info": formatted_info_process
        }
    
    def _save(self):
        # Save processed result in database
        document_store = DocumentStore()
        document_store.save_payload(
            database_name=self.database_name,
            collection_name=self.collection_name,
            payload=self.response
        )





if __name__ == "__main__":
    # Exemplo de uso
    job_id = "job_123"
    metadata = {"user_id": "user_456"}

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

    parser = DocumentParse(
        job_id=job_id,
        metadata=metadata,
        schema=schema,
        config=config,
        file_bytes=file_bytes,
        file_extension="pdf"
    )

    response = parser.run()

    print("\nResposta do parser:")
    print(json.dumps(response, indent=2))

# python -m src.text_parse.module.simple_file_parse