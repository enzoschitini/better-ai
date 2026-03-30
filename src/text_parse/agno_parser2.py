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

json_data = {
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

data = {
    "text": text,
    "task": "Se o nome da empresa for TechNova, troque por BetterAI"
}

config_json = {
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

config = Config()

class AgentParser:
    def __init__(self):
      pass

    def gererate_schemas(self):
        parser = JsonToPydantic("ResearchRequest")
        converter = GeneratePydanticSchema()

        request = parser.parse(data)
        config = parser.parse(config_json)
        output_schema = converter.convert(json_data, "Movie")

        return request, config, output_schema
    
    def run_agent(self, request, config, output_schema):
        agent = Agent(
            model=Groq(id=config.model_id),
            
            instructions=config.instructions,
            description=config.description,
            
            debug_mode=config.debug_mode,
            output_schema=output_schema,
        )

        response = agent.run(input=request)
        return response
    
    def format_response(self, response):
        content = response.content.model_dump()
        metrics_dict = response.metrics.__dict__
        model_metrics = metrics_dict["details"]["model"][0]

        final_response = {
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

        print(json.dumps(final_response, indent=2))

if __name__ == "__main__":
    agent_parser = AgentParser()
    request, config, output_schema = agent_parser.gererate_schemas()
    response = agent_parser.run_agent(request, config, output_schema)
    agent_parser.format_response(response)

# python -m src.text_parse.agno_parser2