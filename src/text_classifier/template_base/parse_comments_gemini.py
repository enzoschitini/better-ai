import json
from typing import List
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

from src.text_classifier.template_base.prompt_loader import PromptLoader

from dotenv import load_dotenv
load_dotenv()


class CommentExtractor:
    def __init__(self):
        self.loader = PromptLoader("src/text_classifier/template_base/prompt.yaml")

        # =====================
        # MODELOS Pydantic
        # =====================
        class Comentario(BaseModel):
            usuario: str = Field(
                title=self.loader.get("parse_comments.usuario.title"),
                description=self.loader.get("parse_comments.usuario.description"),
                examples=self.loader.get("parse_comments.usuario.examples"),
            )

            comentario: str = Field(
                title=self.loader.get("parse_comments.comentario.title"),
                description=self.loader.get("parse_comments.comentario.description"),
                examples=self.loader.get("parse_comments.comentario.examples"),
            )

            likes: int = Field(
                title=self.loader.get("parse_comments.likes.title"),
                description=self.loader.get("parse_comments.likes.description"),
                examples=self.loader.get("parse_comments.likes.examples"),
            )

            replies: int = Field(
                title=self.loader.get("parse_comments.replies.title"),
                description=self.loader.get("parse_comments.replies.description"),
                examples=self.loader.get("parse_comments.replies.examples"),
            )

        class Resposta(BaseModel):
            comentarios: List[Comentario] = Field(
                description="Lista de comentários extraídos"
            )

        self.Comentario = Comentario
        self.Resposta = Resposta

        # =====================
        # OUTPUT PARSER
        # =====================
        self.output_parser = PydanticOutputParser(
            pydantic_object=self.Resposta
        )

        # =====================
        # PROMPT
        # =====================
        self.prompt = PromptTemplate(
            template=(
                "Responda exclusivamente no formato solicitado.\n"
                "{format_instructions}\n\n"
                "Input:\n{input}"
            ),
            input_variables=["input"],
            partial_variables={
                "format_instructions": self.output_parser.get_format_instructions()
            },
        )

        # =====================
        # LLM – GEMINI
        # =====================
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.4,
            convert_system_message_to_human=True,
        )

        # =====================
        # CHAIN
        # =====================
        self.chain = self.prompt | self.llm | self.output_parser

    # =====================
    # PROMPT BASE (inalterado)
    # =====================
    def parse_prompt(self, comments: str) -> str:
        return self.loader.get(
            "context_comments",
            comments=comments,
        )

    # =====================
    # FUNÇÃO PRINCIPAL
    # =====================
    def extract(self, scraper_comments: str):
        input_prompt = self.parse_prompt(scraper_comments)
        resposta = self.chain.invoke({"input": input_prompt})
        return resposta.model_dump()["comentarios"]


# ========================
# EXEMPLO DE USO
# ========================

scraper_comments = """
Comentários sobre o Produto – Simulação de PDF

João Ferreira
Produto excelente! Superou minhas expectativas e chegou antes do prazo.
148

Mariana Alves
Funciona bem, mas achei que poderia vir com mais opções de configuração.
76

Carlos Nogueira
Ótimo custo-benefício. Compraria novamente sem dúvidas!
respostas: 122

Ana Beatriz Costa
Não gostei muito da qualidade do material. Poderia ser mais resistente.
42

Roberto Santos
Sensacional! Uso todos os dias e recomendo para todo mundo.
305

Larissa Moura
Atendeu bem, mas a embalagem veio um pouco amassada.

Vinícius Prado
Simplesmente perfeito. Melhor compra do ano!
277
"""

parser = CommentExtractor()
resultado = parser.extract(scraper_comments)

print(json.dumps(resultado, indent=2, ensure_ascii=False))


# python -m src.text_classifier.template_base.parse_comments_gemini