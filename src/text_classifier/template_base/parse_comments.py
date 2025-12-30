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

class GenericTextExtractor:
    TYPE_MAP = {
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
    }

    def __init__(self, schema: List[dict], model="gpt-4.1-mini", temperature=0.3):
        self.schema = schema

        self.ItemModel = self._build_model("ParsedItem", schema)
        self.ResponseModel = create_model(
            "ParsedResponse",
            items=(List[self.ItemModel], Field(description="Itens extraídos")),
        )

        self.output_parser = PydanticOutputParser(
            pydantic_object=self.ResponseModel
        )

        self.prompt = PromptTemplate(
            template=self._build_prompt(),
            input_variables=["input"],
            partial_variables={
                "format_instructions": self.output_parser.get_format_instructions()
            },
        )

        self.llm = ChatOpenAI(model=model, temperature=temperature)
        self.chain = self.prompt | self.llm | self.output_parser

    # ======================================================
    # MODEL BUILDER (RECURSIVO)
    # ======================================================

    def _build_model(self, model_name: str, schema: List[dict]) -> Type[BaseModel]:
        fields = {}

        for field in schema:
            field_type = field["type"]

            # ---------- OBJECT (NESTED JSON)
            if field_type == "object":
                nested_model = self._build_model(
                    f"{model_name}_{field['name']}",
                    field.get("properties", [])
                )

                fields[field["name"]] = (
                    nested_model,
                    Field(
                        description=field.get("description", ""),
                        default={}
                    ),
                )

            # ---------- LIST
            elif field_type == "list":
                item_def = field["items"]

                if item_def["type"] == "object":
                    item_model = self._build_model(
                        f"{model_name}_{field['name']}_Item",
                        item_def.get("properties", [])
                    )
                    py_type = List[item_model]
                else:
                    py_type = List[self.TYPE_MAP.get(item_def["type"], Any)]

                fields[field["name"]] = (
                    py_type,
                    Field(
                        description=field.get("description", ""),
                        default=[]
                    ),
                )

            # ---------- PRIMITIVE
            else:
                py_type = self.TYPE_MAP.get(field_type, Any)
                default = "" if py_type is str else 0

                fields[field["name"]] = (
                    py_type,
                    Field(
                        description=field.get("description", ""),
                        examples=field.get("examples", []),
                        default=default,
                    ),
                )

        return create_model(model_name, **fields)

    # ======================================================
    # PROMPT
    # ======================================================

    def _build_prompt(self) -> str:
        def describe(schema, indent=0):
            lines = []
            prefix = "  " * indent

            for f in schema:
                if f["type"] == "object":
                    lines.append(f"{prefix}- {f['name']} (object):")
                    lines.extend(describe(f["properties"], indent + 1))
                elif f["type"] == "list":
                    lines.append(f"{prefix}- {f['name']} (list)")
                else:
                    lines.append(
                        f"{prefix}- {f['name']} ({f['type']}): {f.get('description','')}"
                    )
            return lines

        fields_description = "\n".join(describe(self.schema))

        return f"""
Extraia informações estruturadas do texto abaixo conforme o schema.

Campos esperados:
{fields_description}

Regras:
- Respeite a estrutura hierárquica
- Não invente dados
- Campos ausentes devem ser vazios
- Retorne apenas os registros encontrados

{{format_instructions}}

Texto:
{{input}}
"""

    # ======================================================
    # API
    # ======================================================

    def extract(self, text: str) -> List[dict]:
        response = self.chain.invoke({"input": text})
        return response.model_dump()["items"]



# ==========================================================
# EXEMPLO DE USO
# ==========================================================
if __name__ == "__main__":
    with open(f"src/text_classifier/template_base/schema.yaml", "r", encoding="utf-8") as f:
        schema_config = yaml.safe_load(f)

    schema = schema_config["schema_5"]

    extractor = GenericTextExtractor(schema)
    txt_path = "n8n.txt"

    with open(f"src/text_classifier/template_base/txt_examples/{txt_path}", "r", encoding="utf-8") as file:
        scraper = file.read().strip()

    resultado = extractor.extract(scraper)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))



# python -m src.text_classifier.template_base.parse_comments
