import json
from pydantic import BaseModel, Field
from typing import List

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

Larissa Moura Atendeu bem, mas a embalagem veio um pouco amassada.





Vinícius Prado
Simplesmente perfeito. Melhor compra do ano!
277
"""

class GenericTextExtractor:
    """
    Extractor genérico e 100% flexível para parsing estruturado de qualquer texto,
    orientado por schema dinâmico.
    """

    TYPE_MAP = {
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
    }

    def __init__(
        self,
        schema: List[dict],
        model: str = "gpt-4.1-mini",
        temperature: float = 0.3,
    ):
        self.schema = schema

        # === Criação dinâmica dos modelos ===
        self.ItemModel = self._create_item_model()
        self.ResponseModel = self._create_response_model()

        # === Parser ===
        self.output_parser = PydanticOutputParser(
            pydantic_object=self.ResponseModel
        )

        # === Prompt ===
        self.prompt = PromptTemplate(
            template=self._build_prompt(),
            input_variables=["input"],
            partial_variables={
                "format_instructions": self.output_parser.get_format_instructions()
            },
        )

        # === LLM ===
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature
        )

        # === Chain ===
        self.chain = self.prompt | self.llm | self.output_parser

    # ======================================================
    # MODEL BUILDERS
    # ======================================================

    def _create_item_model(self) -> Type[BaseModel]:
        fields = {}

        for field in self.schema:
            py_type = self.TYPE_MAP.get(field["type"], Any)

            default_value = "" if py_type is str else 0

            fields[field["name"]] = (
                py_type,
                Field(
                    title=field.get("title", ""),
                    description=field.get("description", ""),
                    examples=field.get("examples", []),
                    default=default_value,
                ),
            )

        return create_model("ParsedItem", **fields)

    def _create_response_model(self) -> Type[BaseModel]:
        return create_model(
            "ParsedResponse",
            items=(List[self.ItemModel], Field(description="Itens extraídos")),
        )

    # ======================================================
    # PROMPT
    # ======================================================

    def _build_prompt(self) -> str:
        fields_description = "\n".join(
            f"- {f['name']} ({f['type']}): {f.get('description', '')}"
            for f in self.schema
        )

        return f"""
Extraia informações estruturadas do texto abaixo.

Campos esperados:
{fields_description}

Regras:
- Retorne apenas os registros encontrados
- Caso um campo não esteja presente, use string vazia ou 0
- Não invente informações
- Ignore dados irrelevantes

{{format_instructions}}

Texto:
{{input}}
"""

    # ======================================================
    # PUBLIC API
    # ======================================================

    def extract(self, text: str) -> List[dict]:
        response = self.chain.invoke({"input": text})
        return response.model_dump()["items"]


# ==========================================================
# EXEMPLO DE USO
# ==========================================================
if __name__ == "__main__":
    schema = [
        {
            "name": "usuario",
            "type": "str",
            "title": "Usuário",
            "description": "Nome do usuário que escreveu o texto",
            "examples": ["João", "Maria"]
        },
        {
            "name": "comentario",
            "type": "str",
            "title": "Comentário",
            "description": "Texto do comentário",
            "examples": ["Gostei muito!", "Não recomendo"]
        },
        {
            "name": "likes",
            "type": "int",
            "title": "Curtidas",
            "description": "Quantidade de likes",
            "examples": [5, 12]
        }
    ]

    extractor = GenericTextExtractor(schema)

    texto = """
    João
    Gostei muito do conteúdo!
    Likes: 10

    Maria
    Não recomendo.
    Likes: 2
    """

    resultado = extractor.extract(scraper_comments)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))












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













