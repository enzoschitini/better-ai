import json
from typing import List
from pydantic import BaseModel, Field
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers.json import JsonOutputParser
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
from src.text_parse.json_to_pydantic import JsonToPydantic

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

converter = JsonToPydantic()
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