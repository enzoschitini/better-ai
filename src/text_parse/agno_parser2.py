import json
from typing import List
from pydantic import BaseModel, Field
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.groq import Groq
from agno.models.openai import OpenAIResponses
from dotenv import load_dotenv
from src.text_parse.json_to_pydantic import JsonToPydantic, GeneratePydanticSchema
from dataclasses import dataclass, field

load_dotenv()

output_data = {
  "company": {
    "type": "str",
    "description": "Nome da empresa mencionada no texto",
    "example": "TechNova"
  },
  "product": {
    "name": {
      "type": "str",
      "description": "Nome do produto lançado",
      "example": "DataFlow"
    },
    "category": {
      "type": "str",
      "description": "Tipo ou categoria do produto",
      "example": "Aplicativo"
    }
  },
  "purpose": {
    "type": "str",
    "description": "Objetivo principal do produto",
    "example": "Facilitar a análise de dados para pequenas empresas"
  }
}

text = """
Em 2023, a empresa TechNova lançou um novo aplicativo chamado DataFlow. O produto foi desenvolvido em São Paulo e liderado pela engenheira Ana Souza. O objetivo do aplicativo é facilitar a análise de dados para pequenas empresas. Desde o lançamento, o DataFlow já alcançou mais de 50 mil usuários ativos.
"""

input_data = {
    "text": text,
    "task": "Se o nome da empresa for TechNova, troque por BetterAI"
}

config_data = {
    "model_id": "llama-3.3-70b-versatile",
    "debug_mode": True,
    "instructions": "Extraia dados do texto",
    "description": "Leia o texto e extraia as informações relevantes conforme o esquema definido. Retorne um JSON estruturado com os dados extraídos. Caso não encontre alguma informação, retorne null para aquele campo."
}

@dataclass
class Config:
    # Models: OpenAIChat(id="gpt-4.1-mini"), Groq(id="llama-3.3-70b-versatile"),
    model_id: str = "llama-3.3-70b-versatile"
    debug_mode: bool = True

    # Come lo fai
    instructions: str = """
    Extraia dados do texto
    """

    # Cosa sei
    description: str = """
    Leia o texto e extraia as informações relevantes conforme o esquema definido. Retorne um JSON estruturado com os dados extraídos.
    Caso não encontre alguma informação, retorne null para aquele campo.
    """

from typing import Optional, Dict, Any

class AgentParser:
    def __init__(
        self,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        config_data: Optional[Dict[str, Any]] = None,
    ):
        self.input_data = input_data
        self.output_data = output_data
        self.config_data = config_data

        self._generate_schemas()

    def _generate_schemas(self):
        parser = JsonToPydantic()
        converter = GeneratePydanticSchema()

        self.input_schema = parser.parse(self.input_data)
        self.output_schema = converter.convert(self.output_data, "OutputSchema")

        if self.config_data is not None:
            self.config_schema = parser.parse(self.config_data)
        else:
            self.config_schema = Config()

    def get_schemas(self):
        return {
            "input": self.input_schema,
            "output": self.output_schema,
            "config": self.config_schema,
        }

    def run_agent(self):
        agent = Agent(
            model=Groq(id=self.config_schema.model_id),
            instructions=self.config_schema.instructions,
            description=self.config_schema.description,
            debug_mode=self.config_schema.debug_mode,
            output_schema=self.output_schema,
        )

        response = agent.run(input=self.input_schema)
        return response
    
    def format_response(self, raw_response):
        content = raw_response.content.model_dump()
        metrics_dict = raw_response.metrics.__dict__
        model_metrics = metrics_dict["details"]["model"][0]

        response = {
            "content": content,
            "metadata": {
                "model": {
                    "provider": model_metrics.provider,
                    "id": model_metrics.id
                },
                "metrics": {
                    "input_tokens": model_metrics.input_tokens,
                    "output_tokens": model_metrics.output_tokens,
                    "total_tokens": model_metrics.total_tokens,
                },
                "duration": round(metrics_dict.get("duration"), 2),
            }
        }

        print(json.dumps(response, indent=2))
        return response

if __name__ == "__main__":
    agent_parser = AgentParser(
        input_data=input_data,
        output_data=output_data,
        config_data=config_data
    )
    content_parsed = agent_parser.run_agent()
    response = agent_parser.format_response(content_parsed)

# python -m src.text_parse.agno_parser2