import json
from pydantic import BaseModel, Field
from typing import List
import yaml

from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

from typing import List, Any, Type
from pydantic import BaseModel, Field, create_model
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser

from src.text_classifier.template_base.prompt_loader import PromptLoader

from dotenv import load_dotenv
load_dotenv()


class CommentExtractor:
    def __init__(self):
        self.loader = PromptLoader("src/text_classifier/template_base/prompt.yaml")

        # === Classes originais ===
        class Comentario(BaseModel):
            
            comentario: str = Field(
                title=self.loader.get("parse_comments.comentario.title"),
                description=self.loader.get("parse_comments.comentario.description"),
                examples=self.loader.get("parse_comments.comentario.examples"))

            likes: int = Field(
                title=self.loader.get("parse_comments.likes.title"),
                description=self.loader.get("parse_comments.likes.description"),
                examples=self.loader.get("parse_comments.likes.examples"))

        class Resposta(BaseModel):
            comentarios: List[Comentario] = Field(description="Lista de comentários extraídos")

        self.Comentario = Comentario
        self.Resposta = Resposta

        # Cria o parser
        self.output_parser = PydanticOutputParser(pydantic_object=self.Resposta)

        # Template original da sua chain
        self.prompt = PromptTemplate(
            template="Responda de forma estruturada.\n{format_instructions}\nInput: {input}",
            input_variables=["input"],
            partial_variables={"format_instructions": self.output_parser.get_format_instructions()},
        )

        # Modelo original
        self.llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0.4)

        self.chain = self.prompt | self.llm | self.output_parser

    # === Prompt ORIGINAL, sem mexer em nada ===
    def parse_prompt(self, comments):
        prompt = self.loader.get(
            "context_comments",
            comments=comments
        )

        return prompt
    
    # === Função principal ===
    def extract(self, scraper_comments):
        input_prompt = self.parse_prompt(scraper_comments)
        resposta = self.chain.invoke({"input": input_prompt})
        return resposta.model_dump()["comentarios"]


# ========================
# Exemplo de uso
# ========================

"""
query = "Extrair comentários individuais do texto original."

parser = CommentExtractor()
resultado = parser.extract(scraper_comments)

print(json.dumps(resultado, indent=2, ensure_ascii=False))
#"""

# python -m src.text_classifier.template_base.parse_comments













