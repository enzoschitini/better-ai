import json
from pydantic import BaseModel, Field
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from dotenv import load_dotenv
from src.text_parse.list_schemas.pydantic_schema import GeneratePydanticSchema

load_dotenv()

# 🔹 Json Schema

output_data = {
    "title": {
        "type": "str",
        "description": "Title of the content"
    },
    "author": {
        "type": "str",
        "description": "Author of the content"
    },
    "summary": {
        "type": "str",
        "description": "Short summary of the text"
    },
    "code": {
        "type": "str",
        "description": "Code snippet extracted from the text",
        #"required": True
    },
    "names": {
        "type": "list",
        "description": "List of names mentioned in the text",
        "items": {
            "type": "str",
            "description": "A person's name mentioned in the text"
        }
    },

    "peoples": {
        "type": "list",
        "description": "List of people with structured details extracted from the text",
        "max_length": 1,
        "items": {
            "type": "object",
            "description": "A person mentioned in the text",
            "properties": {
                "name": {
                    "type": "str",
                    "description": "Full name of the person"
                },
                "experience": {
                    "type": "str",
                    "description": "Years of experience or expertise level"
                },
                "profession": {
                    "type": "str",
                    "description": "Profession or role of the person"
                }
            }
        }
    }
}

converter = GeneratePydanticSchema()
output_schema = converter.convert(output_data, "OutputSchema")

# print("Generated Pydantic Schema:")
# print(output_schema.schema_json(indent=2))

# 🔹 Schema do que você quer extrair
from typing import Optional

class PeoplesDescription(BaseModel):
    name: str = Field(description="Name of the person")
    experience: str = Field(description="Experience of the person in years")
    profession: str = Field(description="Profession of the person")

class ParsedText(BaseModel):
    title: str = Field(description="Title of the content")
    author: str = Field(description="Author of the content")
    summary: str = Field(description="Short summary of the text")
    code: Optional[str] = Field(
        default=None,
        description="Code snippet extracted from the text"
    )
    names: list[str] = Field(description="List of names mentioned in the text")
    peoples: list[PeoplesDescription] = Field(
        description="List of people with their descriptions.",
        max_length=5
    )

output_schema2 = ParsedText

agent = Agent(
    model=OpenAIResponses(id="gpt-4.1-mini"),
    output_schema=output_schema,
)

# 🔹 Texto de entrada (pode vir de arquivo, API, etc.)
input_text = """
Title: The Future of AI
Author: John Doe
Code: 

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