import json
from pydantic import BaseModel, Field
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from dotenv import load_dotenv

load_dotenv()

class MovieScript(BaseModel):
    setting: str = Field(description="Where the movie takes place")
    genre: str = Field(description="Movie genre")
    storyline: str = Field(description="Brief plot summary")

agent = Agent(
    model=OpenAIResponses(id="gpt-4.1-mini"),
    output_schema=MovieScript,
)

response = agent.run("Write a movie script about a heist in Tokyo")

# response.content is a MovieScript object, not a string
print("\n\nResponse:")
print(response.content.setting)    # "Tokyo, Japan - 2024"
print(response.content.genre)      # "Action/Thriller"
print(response.content.storyline)  # "A retired thief is pulled back..."

print("\n\nFull Response Object:")
print(json.dumps(response.content.__dict__, indent=2))  # This will show the full OpenAI response, including metadata
print(json.dumps(response.metrics.__dict__, indent=2, default=str))

# python -m src.text_parse.agno_parser