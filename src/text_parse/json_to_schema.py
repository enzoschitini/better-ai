from typing import Any, Dict, List, Type
from pydantic import BaseModel, Field, create_model
import inflect

p = inflect.engine()


# ==============================
# Strategy: Type Resolver
# ==============================
class TypeResolver:
    def resolve(self, value: Any) -> Any:
        raise NotImplementedError


class DefaultTypeResolver(TypeResolver):
    def resolve(self, value: Any) -> Any:
        if isinstance(value, str):
            return str
        elif isinstance(value, bool):
            return bool
        elif isinstance(value, int):
            return int
        elif isinstance(value, float):
            return float
        elif isinstance(value, list):
            return list
        elif isinstance(value, dict):
            return dict
        else:
            return Any


# ==============================
# Helper: Name Generator
# ==============================
class NameGenerator:
    def __init__(self):
        self.counter = 0

    def generate(self, base: str) -> str:
        self.counter += 1
        return f"{base.capitalize()}{self.counter}"


# ==============================
# Builder: Schema Builder
# ==============================
class SchemaBuilder:
    def __init__(self):
        self.models: Dict[str, Type[BaseModel]] = {}

    def create_model(self, name: str, fields: Dict[str, tuple]) -> Type[BaseModel]:
        model = create_model(name, **fields)
        self.models[name] = model
        return model

    def get_models(self):
        return self.models


# ==============================
# Core: JsonToSchema
# ==============================
class JsonToSchema:
    def __init__(
        self,
        type_resolver: TypeResolver = None,
        name_generator: NameGenerator = None,
        builder: SchemaBuilder = None,
    ):
        self.type_resolver = type_resolver or DefaultTypeResolver()
        self.name_generator = name_generator or NameGenerator()
        self.builder = builder or SchemaBuilder()

    # --------------------------
    # Public API
    # --------------------------
    def convert(self, data: Dict[str, Any], root_name: str = "RootModel") -> Type[BaseModel]:
        return self._parse_object(data, root_name)

    def get_all_models(self) -> Dict[str, Type[BaseModel]]:
        return self.builder.get_models()

    # --------------------------
    # Internal Parsing
    # --------------------------
    def _parse_object(self, obj: Dict[str, Any], name: str) -> Type[BaseModel]:
        fields = {}

        for key, value in obj.items():
            field_type, field_info = self._parse_field(key, value)
            fields[key] = (field_type, field_info)

        return self.builder.create_model(name, fields)

    def _parse_field(self, key: str, value: Any):
        description = f"Auto-generated field for {key}"

        # Nested object
        if isinstance(value, dict):
            nested_name = self.name_generator.generate(key)
            nested_model = self._parse_object(value, nested_name)
            return nested_model, Field(description=description)

        # List handling
        elif isinstance(value, list):
            if len(value) == 0:
                return List[Any], Field(description=description)

            first_item = value[0]

            if isinstance(first_item, dict):
                nested_name = self.name_generator.generate(p.singular_noun(key) or key)
                nested_model = self._parse_object(first_item, nested_name)
                return List[nested_model], Field(description=description)

            else:
                resolved_type = self.type_resolver.resolve(first_item)
                return List[resolved_type], Field(description=description)

        # Primitive
        else:
            resolved_type = self.type_resolver.resolve(value)
            return resolved_type, Field(description=description)

if __name__ == "__main__":
    import json

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
    Movie = converter.convert(json_data, "Movie")

    # Teste 1: criar instância
    movie_instance = Movie(**json_data)

    print(movie_instance)

    # Teste 2: acessar atributos
    print(movie_instance.script.genre)

    # Teste 3: validação automática
    try:
        Movie(script={"setting": 123})  # erro esperado
    except Exception as e:
        print("Erro esperado:", e)

# python -m src.text_parse.json_to_schema
# inflect==7.5.0