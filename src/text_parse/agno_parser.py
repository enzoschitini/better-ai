import json
from typing import List
from pydantic import BaseModel, Field
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from dotenv import load_dotenv
from src.text_parse.json_to_schema import JsonToSchema

load_dotenv()

json_data = {
    "script": {
        "setting": "Tokyo",
        "genre": "Heist",
        "storyline": "A big robbery"
    },
    "context": {
        "history": "Ancient artifact",
        "local": "Museum",
        "year": 2025
    },
    "people": {
        "characters": [
            {
                "name": "John",
                "role": "protagonist",
                "description": "Smart thief"
            }
        ]
    }
}

converter = JsonToSchema()
Movie = converter.convert(json_data, "Movie")

# 🤖 Agent
agent = Agent(
    model=OpenAIResponses(id="gpt-4.1-mini"),
    output_schema=Movie,
)

response = agent.run("Write a movie script about a heist in Tokyo with detailed 2 characters")

# 📦 JSON completo
print("\n\nFull Response Object:")
print(json.dumps(response.content.model_dump(), indent=2))

print("\n\nMetrics:")
print(json.dumps(response.metrics.__dict__, indent=2, default=str))

# python -m src.text_parse.agno_parser