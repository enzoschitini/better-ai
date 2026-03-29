import json
from typing import List
from pydantic import BaseModel, Field
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from dotenv import load_dotenv
from text_parse.json_to_pydantic import JsonToPydantic

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
  "launch": {
    "year": {
      "type": "int",
      "description": "Ano de lançamento do produto",
      "example": 2023
    },
    "location": {
      "type": "str",
      "description": "Cidade onde o produto foi desenvolvido",
      "example": "São Paulo"
    }
  },
  "team": {
    "leader": {
      "type": "str",
      "description": "Nome da pessoa responsável pelo projeto",
      "example": "Ana Souza"
    }
  },
  "metrics": {
    "active_users": {
      "type": "int",
      "description": "Número de usuários ativos mencionados",
      "example": 50000
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

converter = JsonToPydantic()
Movie = converter.convert(json_data, "Movie")

# 🤖 Agent
agent = Agent(
    model=OpenAIResponses(id="gpt-4.1-mini"),
    output_schema=Movie,
)

response = agent.run(
    input=text,
    instructions="Extraia dados do texto"
)

# 📦 JSON completo
print("\n\nFull Response Object:")
print(json.dumps(response.content.model_dump(), indent=2))

print("\n\nMetrics:")
print(json.dumps(response.metrics.__dict__, indent=2, default=str))

# python -m src.text_parse.agno_parser