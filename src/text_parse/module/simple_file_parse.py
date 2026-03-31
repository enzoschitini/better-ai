import json
from typing import Optional
from fastapi import HTTPException
from io import BytesIO

from src.embedding.services.file_content_extractor import FileContentExtractor
from src.text_parse.content_parsing_agent import ContentParsingAgent

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

    def run(self):
        try:
            schema_data = json.loads(self.schema)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in schema")

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

        if self.config:
            try:
                config_input = json.loads(self.config)
                config_data = {**default_config, **config_input}
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON in config")
        else:
            config_data = default_config

        extractor = FileContentExtractor(
            file_bytes=self.file_bytes,
            file_extension=self.file_extension
        )
        result_extract = extractor.extract()

        agent_parser = ContentParsingAgent(
            input_data={
                "file_content": result_extract["response"]
            },
            output_data=schema_data,
            config_data=config_data
        )

        content_parsed = agent_parser.run_agent()
        response = agent_parser.format_response(content_parsed)

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

    with open("example.pdf", "rb") as f:
        file_bytes = BytesIO(f.read())

    parser = SimpleFileParse(
        schema=schema,
        config=config,
        file_bytes=file_bytes,
        file_extension="pdf"
    )

    response = parser.run()

# python -m src.text_parse.module.simple_file_parse