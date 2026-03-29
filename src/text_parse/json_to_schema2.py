from typing import Any, Dict, List, Type, Tuple
from pydantic import BaseModel, Field, create_model
import inflect

p = inflect.engine()


# ==========================================
# Strategy: Type Resolver
# ==========================================
class TypeResolver:
    def resolve(self, value: Any) -> Any:
        raise NotImplementedError


class DefaultTypeResolver(TypeResolver):
    def resolve(self, value: Any) -> Any:
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


# ==========================================
# Helper: Name Generator
# ==========================================
class NameGenerator:
    def __init__(self):
        self.counter = 0

    def generate(self, base: str) -> str:
        self.counter += 1
        return f"{base.capitalize()}{self.counter}"


# ==========================================
# Builder: Schema Builder
# ==========================================
class SchemaBuilder:
    def __init__(self):
        self.models: Dict[str, Type[BaseModel]] = {}

    def create(self, name: str, fields: Dict[str, Tuple[Any, Any]]) -> Type[BaseModel]:
        model = create_model(name, **fields)
        self.models[name] = model
        return model

    def get_all(self) -> Dict[str, Type[BaseModel]]:
        return self.models


# ==========================================
# Parser: Field Metadata (🔥 NOVO)
# ==========================================
class FieldMetadataParser:
    def parse(self, key: str, value: Any) -> Tuple[Any, Any] | None:
        """
        Detecta se o campo é um schema explícito:
        {
            "type": "str",
            "description": "...",
            "example": "...",
            "default": ...
        }
        """
        if isinstance(value, dict) and "type" in value:
            return self._parse_metadata(value)

        return None

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


# ==========================================
# Core: JsonToSchema
# ==========================================
class JsonToSchema:
    def __init__(
        self,
        type_resolver: TypeResolver = None,
        name_generator: NameGenerator = None,
        builder: SchemaBuilder = None,
        metadata_parser: FieldMetadataParser = None,
    ):
        self.type_resolver = type_resolver or DefaultTypeResolver()
        self.name_generator = name_generator or NameGenerator()
        self.builder = builder or SchemaBuilder()
        self.metadata_parser = metadata_parser or FieldMetadataParser()

    # --------------------------------------
    # Public API
    # --------------------------------------
    def convert(self, data: Dict[str, Any], root_name: str = "RootModel") -> Type[BaseModel]:
        return self._parse_object(data, root_name)

    def get_models(self) -> Dict[str, Type[BaseModel]]:
        return self.builder.get_all()

    # --------------------------------------
    # Internal Parsing
    # --------------------------------------
    def _parse_object(self, obj: Dict[str, Any], name: str) -> Type[BaseModel]:
        fields = {}

        for key, value in obj.items():
            fields[key] = self._parse_field(key, value)

        return self.builder.create(name, fields)

    def _parse_field(self, key: str, value: Any) -> Tuple[Any, Any]:
        # 🔥 1. Metadata explícita
        metadata = self.metadata_parser.parse(key, value)
        if metadata:
            return metadata

        description = f"Auto-generated field for {key}"

        # ----------------------------------
        # Nested Object
        # ----------------------------------
        if isinstance(value, dict):
            model_name = self.name_generator.generate(key)
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
                model_name = self.name_generator.generate(
                    p.singular_noun(key) or key
                )
                nested_model = self._parse_object(first, model_name)
                return List[nested_model], ...

            # Lista de primitivos
            item_type = self.type_resolver.resolve(first)
            return List[item_type], Field(description=description)

        # ----------------------------------
        # Primitive
        # ----------------------------------
        field_type = self.type_resolver.resolve(value)
        return field_type, Field(description=description)


# ==========================================
# Example Usage
# ==========================================
if __name__ == "__main__":
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

    converter = JsonToSchema()
    Movie = converter.convert(json_data, "Movie")

    print(Movie.schema_json(indent=2))

# python -m src.text_parse.json_to_schema2
# inflect==7.5.0