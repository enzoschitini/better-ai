import json
from typing import List
from pydantic import BaseModel, Field
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers.json import JsonOutputParser
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
from src.text_parse.pydantic_schema import JsonToPydantic

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
        "Extraia dados do texto"
        "Texto: {text}\n\n"
        "Leia o texto e extraia as informações relevantes conforme o esquema definido. Retorne um JSON estruturado com os dados extraídos."
        "A resposta deve ser estruturada no formato JSON.\n"
        "{format_instructions}\n\n"
    ),
    input_variables=["text"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

# === Modelo ===
llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)

# === Encadeia ===
chain = prompt | llm | parser

text = """
Em 2023, a empresa TechNova lançou um novo aplicativo chamado DataFlow. O produto foi desenvolvido em São Paulo e liderado pela engenheira Ana Souza. O objetivo do aplicativo é facilitar a análise de dados para pequenas empresas. Desde o lançamento, o DataFlow já alcançou mais de 50 mil usuários ativos.
"""

# === Teste ===
resposta = chain.invoke({"text": text})
print(json.dumps(resposta, indent=2, ensure_ascii=False))



# python -m src.text_parse.lang_parser