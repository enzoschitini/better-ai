import json
from pydantic import BaseModel, Field
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from dotenv import load_dotenv
from src.text_parse.list_schemas.pydantic_schema import GeneratePydanticSchema

load_dotenv()

# 🔹 Schema do que você quer extrair

class PeoplesDescription(BaseModel):
    name: str = Field(description="Name of the person")
    experience: str = Field(description="Experience of the person in years")
    profession: str = Field(description="Profession of the person")

class ParsedText(BaseModel):
    title: str = Field(description="Title of the content")
    author: str = Field(description="Author of the content")
    summary: str = Field(description="Short summary of the text")
    names: list[str] = Field(description="List of names mentioned in the text")
    peoples: list[PeoplesDescription] = Field(description="List of people with their descriptions.", max_length=5)

output_schema = ParsedText

# 🔹 Json Schema

output_data = {
    "title": {"type": "str"},
    "author": {"type": "str"},
    "summary": {"type": "str"},

    "names": {
        "type": "list",
        "items": {
            "type": "str"
        }
    },

    "peoples": {
        "type": "list",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "str"},
                "experience": {"type": "str"},
                "profession": {"type": "str"}
            }
        }
    }
}

converter = GeneratePydanticSchema()
output_schema = converter.convert(output_data, "OutputSchema")

print("Generated Pydantic Schema:")
print(output_schema.schema_json(indent=2))

agent = Agent(
    model=OpenAIResponses(id="gpt-4.1-mini"),
    output_schema=output_schema,
)

# 🔹 Texto de entrada (pode vir de arquivo, API, etc.)
input_text = """
Title: The Future of AI
Author: John Doe

Artificial Intelligence is evolving rapidly. Companies are investing heavily
in automation and machine learning to improve efficiency and decision-making.

Enzo: Is a data scientist and has 5 years of experience
Laura: Is a software engineer and has 3 years of experience
Marico: Is a product manager and has 7 years of experience.
"""

# 🔹 Prompt agora é de EXTRAÇÃO, não geração
prompt = f"""
Extract the following structured information from the text below.

Text:
{input_text}
"""

response = agent.run(prompt)

print("Parsed Output:")
parsed_dict = response.content.model_dump()
print(json.dumps(parsed_dict, indent=2))

# python -m src.text_parse.list_schemas.list_schema