import json
from typing import List
from pydantic import BaseModel, Field
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers.json import JsonOutputParser
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
from src.text_parse.json_to_schema import JsonToSchema

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
Movie_Schema = converter.convert(json_data, "Movie")


# === Parser com Pydantic ===
parser = JsonOutputParser(pydantic_object=Movie_Schema)

# === Prompt ===
prompt = PromptTemplate(
    template=(
        "A partir de uma ideia, gere uma história completa e estruturada no formato JSON.\n"
        "{format_instructions}\n\n"
        "⚠️ Instruções específicas:\n"
        "- Em 'contexto.caracteristicas', escreva descrições detalhadas e personificadas.\n"
        "- Cada item da lista deve trazer uma característica quase como se fosse uma pequena cena ou sensação.\n\n"
        "Ideia: {ideia}"
    ),
    input_variables=["ideia"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

# === Modelo ===
llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)

# === Encadeia ===
chain = prompt | llm | parser

# === Teste ===
resposta = chain.invoke({"ideia": "Um bosque mágico"})
print(json.dumps(resposta, indent=2, ensure_ascii=False))



# python -m src.text_parse.lang_parser