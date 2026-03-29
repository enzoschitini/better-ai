import json
from typing import List
from pydantic import BaseModel, Field
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from dotenv import load_dotenv

load_dotenv()


# 🎬 Parte 1: Estrutura do roteiro
class MovieScript(BaseModel):
    setting: str = Field(description="Where the movie takes place")
    genre: str = Field(description="Movie genre")
    storyline: str = Field(description="Brief plot summary")

class MovieContext(BaseModel):
    history: str = Field(description="Background information about the movie's universe")
    local: str = Field(description="Specific location within the movie's universe")
    year: int = Field(description="Year in which the movie is set")

# 🎭 Parte 2: Personagens
class Character(BaseModel):
    name: str = Field(description="Character name")
    role: str = Field(description="Role in the story (e.g., protagonist, antagonist)")
    description: str = Field(description="Short description of the character")


class MoviePerson(BaseModel):
    characters: List[Character] = Field(description="List of characters in the movie")


# 🎬🎭 Parte 3: Modelo final (composição)
class Movie(BaseModel):
    script: MovieScript
    people: MoviePerson
    context: MovieContext


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