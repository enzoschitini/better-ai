import json
from typing import List
from pydantic import BaseModel
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers.json import JsonOutputParser
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv

load_dotenv()

# === Modelo Pydantic para saída estruturada ===
class Contexto(BaseModel):
    descricao: str
    lenda: str
    caracteristicas: List[str]  # continua sendo lista de strings

class Protagonista(BaseModel):
    nome: str
    descricao: str
    motivacao: str

class Personagens(BaseModel):
    protagonista: Protagonista
    aliados: List[str]

class Narrativa(BaseModel):
    introducao: str
    desenvolvimento: str
    conflito: str
    resolucao: str

class Historia(BaseModel):
    titulo: str
    subtitulo: str
    contexto: Contexto
    personagens: Personagens
    narrativa: Narrativa
    temas: List[str]


# === Parser com Pydantic ===
parser = JsonOutputParser(pydantic_object=Historia)

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