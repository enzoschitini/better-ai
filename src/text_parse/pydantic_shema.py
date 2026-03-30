from typing import Any, Dict, List, Type, Tuple
from pydantic import BaseModel, Field, create_model
from typing import Any, Dict, Type
from pydantic import BaseModel, create_model
import inflect

inflector = inflect.engine()

class FieldMetadataParser:
    def parse(self, value: Any) -> Tuple[Any, Any] | None:
        try:
            if isinstance(value, dict) and "type" in value:
                return self._parse_metadata(value)
            return None
        
        except Exception as e:
            raise RuntimeError("Error parsing field metadata", str(e))

    def _parse_metadata(self, value: Dict[str, Any]) -> Tuple[Any, Any]:
        field_type = self._map_type(value.get("type"))

        field_info = Field(
            default=value.get("default", ...),
            description=value.get("description"),
            examples=[value["example"]] if "example" in value else None
        )

        return field_type, field_info

    def _map_type(self, type_name: str):
        mapping = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
        }
        return mapping.get(type_name, Any)


class JsonToPydantic:
    def __init__(self, model_name: str = "DynamicModel"):
        self.model_name = model_name

    def _infer_type(self, value: Any) -> Type:
        try:
            if isinstance(value, str):
                return str
            elif isinstance(value, int):
                return int
            elif isinstance(value, float):
                return float
            elif isinstance(value, bool):
                return bool
            elif isinstance(value, list):
                return list
            elif isinstance(value, dict):
                return dict
            else:
                return Any
        except Exception as e:
            raise RuntimeError("Error inferring type", str(e))

    def build_model(self, data: Dict[str, Any]) -> Type[BaseModel]:
        try:
            fields = {}

            for key, value in data.items():
                field_type = self._infer_type(value)
                fields[key] = (field_type, ...)

            return create_model(self.model_name, **fields)
        except Exception as e:
            raise RuntimeError("Error building model", str(e))

    def parse(self, data: Dict[str, Any]) -> BaseModel:
        try:
            model = self.build_model(data)
            return model(**data)
        except Exception as e:
            raise RuntimeError("Error parsing data", str(e))


class GeneratePydanticSchema:
    def __init__(self, metadata_parser: FieldMetadataParser = None):
        self.metadata_parser = metadata_parser or FieldMetadataParser()

        # Estado interno
        self._models: Dict[str, Type[BaseModel]] = {}
        self._name_counter = 0

    # --------------------------------------
    # Public API
    # --------------------------------------
    def convert(self, data: Dict[str, Any], root_name: str = "RootModel") -> Type[BaseModel]:
        try:
            return self._parse_object(data, root_name)
        except Exception as e:
            raise RuntimeError("Error converting data", str(e))

    def get_models(self) -> Dict[str, Type[BaseModel]]:
        return self._models

    # --------------------------------------
    # Helpers internos
    # --------------------------------------
    def _generate_name(self, base: str) -> str:
        self._name_counter += 1
        return f"{base.capitalize()}{self._name_counter}"

    def _create_model(self, name: str, fields: Dict[str, Tuple[Any, Any]]) -> Type[BaseModel]:
        model = create_model(name, **fields)
        self._models[name] = model
        return model

    def _resolve_type(self, value: Any) -> Any:
        if isinstance(value, str):
            return str
        if isinstance(value, bool):
            return bool
        if isinstance(value, int):
            return int
        if isinstance(value, float):
            return float
        if isinstance(value, list):
            return list
        if isinstance(value, dict):
            return dict
        return Any

    # --------------------------------------
    # Parsing
    # --------------------------------------
    def _parse_object(self, obj: Dict[str, Any], name: str) -> Type[BaseModel]:
        fields = {}

        for key, value in obj.items():
            fields[key] = self._parse_field(key, value)

        return self._create_model(name, fields)

    def _parse_field(self, key: str, value: Any) -> Tuple[Any, Any]:
        try:
            metadata = self.metadata_parser.parse(value)
            if metadata:
                return metadata

            description = f"Auto-generated field for {key}"

            # ----------------------------------
            # Nested Object
            # ----------------------------------
            if isinstance(value, dict):
                model_name = self._generate_name(key)
                nested_model = self._parse_object(value, model_name)
                return nested_model, ...

            # ----------------------------------
            # List
            # ----------------------------------
            if isinstance(value, list):
                if not value:
                    return List[Any], Field(description=description)

                first = value[0]

                # Lista de objetos
                if isinstance(first, dict):
                    model_name = self._generate_name(
                        inflector.singular_noun(key) or key
                    )
                    nested_model = self._parse_object(first, model_name)
                    return List[nested_model], ...

                # Lista de primitivos
                item_type = self._resolve_type(first)
                return List[item_type], Field(description=description)

            # ----------------------------------
            # Primitive
            # ----------------------------------
            field_type = self._resolve_type(value)
            return field_type, Field(description=description)
        except Exception as e:
            raise RuntimeError("Error parsing field", str(e))




# ==========================================
# Example Usage
# ==========================================
def TestFieldMetadataParser():
    parser = FieldMetadataParser()

    test_cases = [
        {
            "input": {
                "type": "str",
                "description": "Nome do personagem",
                "example": "John"
            }
        },
        {
            "input": {
                "type": "int",
                "default": 10
            }
        },
        {
            "input": "valor simples"
        }
    ]

    for i, case in enumerate(test_cases, 1):
        result = parser.parse(case["input"])
        print(f"\nTeste {i}")
        print("Input:", case["input"])
        print("Output:", result)

def TestJsonToPydantic():
    data = {
        "text": "A empresa TechNova está crescendo rapidamente.",
        "task": "Se o nome da empresa for TechNova, troque por BetterAI"
    }
    parser = JsonToPydantic("ResearchRequest")
    request = parser.parse(data)
    
    print(request)
    print(type(request))

def TestGeneratePydanticSchema():
    json_data = {
        "script": {
            "setting": {
                "type": "str",
                "description": "Onde o filme acontece",
                "example": "Tokyo"
            },
            "genre": {
                "type": "str",
                "description": "Gênero do filme",
                "example": "Heist"
            },
            "storyline": "A big robbery"
        },
        "context": {
            "year": {
                "type": "int",
                "description": "Ano da história",
                "example": 2025
            }
        },
        "people": {
            "characters": [
                {
                    "name": {
                        "type": "str",
                        "description": "Nome do personagem"
                    },
                    "role": "protagonist"
                }
            ]
        }
    }

    converter = JsonToPydantic()
    Movie = converter.convert(json_data, "Movie")

    print(Movie.schema_json(indent=2))


# python -m src.text_parse.pydantic_shema
# inflect==7.5.0