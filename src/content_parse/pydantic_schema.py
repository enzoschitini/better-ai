import inflect
from typing import Any, Dict, List, Type, Tuple, Optional
from pydantic import BaseModel, Field, create_model

inflector = inflect.engine()


class JsonToPydantic:
    """
    Classe para converter um dicionário JSON em um modelo Pydantic dinâmico, identificando automaticamente os tipos dos campos.

    Args: 
    :param model_name (str): Nome do modelo Pydantic a ser criado. Default é "DynamicModel".

    Methods:
        build_model(): Constrói um modelo Pydantic dinâmico baseado no dicionário JSON fornecido.
        parse(): Converte um dicionário JSON em uma instância do modelo Pydantic gerado.
    """
    def __init__(self, model_name: str = "DynamicModel"):
        self.model_name = model_name

    def _infer_type(self, value: Any) -> Type:
        """
        Identifica e retorna o tipo Python correspondente ao valor fornecido, como str, int, float, bool, list, dict ou Any.

        Args: 
        value (Any): O valor para o qual o tipo deverá ser inferido.

        Returns:
                Type: O tipo Python correspondente ao valor.
        
        Raises:
                RuntimeError: Caso ocorra algum erro durante a inferência do tipo.
        """
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
        """
        Constrói e retorna um modelo Pydantic dinamicamente, com campos tipados de acordo com os dados fornecidos.

        Args: 
        data (Dict[str, Any]): Dicionário contendo os dados para os quais o modelo será criado.

        Returns:
                Type[BaseModel]: Classe do modelo Pydantic gerado dinamicamente.
        
        Raises:
                RuntimeError: Caso ocorra algum erro durante a construção do modelo.
        """
        try:
            fields = {}

            for key, value in data.items():
                field_type = self._infer_type(value)
                fields[key] = (field_type, ...)

            return create_model(self.model_name, **fields)
        except Exception as e:
            raise RuntimeError("Error building model", str(e))

    def parse(self, data: Dict[str, Any]) -> BaseModel:
        """
        Gera um modelo Pydantic baseado nos dados fornecidos e retorna uma instância desse modelo preenchida com os dados.

        Args: 
        data (Dict[str, Any]): Dicionário JSON a ser convertido em uma instância do modelo Pydantic.

        Returns:
                BaseModel: Instância do modelo Pydantic com os dados fornecidos.
        
        Raises:
                RuntimeError: Caso ocorra algum erro durante o parsing dos dados para o modelo.
        """
        try:
            model = self.build_model(data)
            return model(**data)
        except Exception as e:
            raise RuntimeError("Error parsing data", str(e))


class FieldMetadataParser:
    """
    Classe responsável por analisar metadados de campos a partir de dicionários e convertê-los em tipos e campos do Pydantic. 
    Permite interpretar definições de tipo, requisitos e outras propriedades, gerando estruturas apropriadas para validação.

    Methods:
            parse(): Analisa o valor fornecido e retorna uma tupla com tipo e informações do campo, ou None se não for metadado.
    """

    def parse(self, value: Any) -> Tuple[Any, Any] | None:
        try:
            if isinstance(value, dict) and "type" in value:
                return self._parse_metadata(value)
            return None
        
        except Exception as e:
            raise RuntimeError("Error parsing field metadata", str(e))

    def _parse_metadata(self, value: Dict[str, Any]) -> Tuple[Any, Any]:
        """
        Analisa um dicionário de metadados e retorna o tipo do campo e um objeto Field configurado conforme as propriedades do dicionário.

        Args: 
        value (Dict[str, Any]): Dicionário contendo as propriedades do campo, como 'type', 'required', 'items', etc.

        Returns:
                Tuple[Any, Any]: Uma tupla com o tipo do campo e as informações adicionais formatadas em um objeto Field.

        Raises:
                ValueError: Se um tipo 'list' não definir o campo obrigatório 'items'.
        """
        type_name = value.get("type")
        is_required = value.get("required", False)

        if type_name == "list":
            items = value.get("items")

            if not items:
                raise ValueError("List type must define 'items'")

            if items.get("type") != "object":
                item_type = self._map_type(items.get("type"))
                field_type = List[item_type]
            else:
                properties = items.get("properties", {})
                model_name = "NestedItem"

                nested_model = create_model(
                    model_name,
                    **{
                        k: (
                            self._map_type(v["type"]),
                            Field(description=v.get("description"))
                        )
                        for k, v in properties.items()
                    }
                )

                field_type = List[nested_model]

        else:
            field_type = self._map_type(type_name)

        if not is_required:
            field_type = Optional[field_type]

        field_info = Field(
            default=value.get("default", None if not is_required else ...),
            description=value.get("description"),
            examples=[value["example"]] if "example" in value else None,
            min_length=value.get("min_length"),
            max_length=value.get("max_length"),
        )

        return field_type, field_info

    def _map_type(self, type_name: str):
        """
        Mapeia uma string representando um tipo para o tipo Python correspondente usado na modelagem de dados.

        Args:
        type_name (str): Nome do tipo em formato de string, como 'str', 'int', etc.

        Returns:
                Tipo Python correspondente ao nome fornecido, ou Any se o tipo não for reconhecido.
        """
        mapping = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
        }
        return mapping.get(type_name, Any)


class GeneratePydanticSchema:
    """
    Classe responsável por converter dicionários aninhados em modelos Pydantic de forma dinâmica,
    facilitando a geração automática de schemas para validação de dados complexos.

    Args: 
    :param metadata_parser (FieldMetadataParser): Objeto utilizado para parsear metadata de campos. Default é uma instância nova de FieldMetadataParser.

    Methods:
            convert(): Converte um dicionário em um modelo Pydantic raiz.
            get_models(): Retorna todos os modelos Pydantic gerados até o momento.
    """
    def __init__(self, metadata_parser: FieldMetadataParser = None):
        self.metadata_parser = metadata_parser or FieldMetadataParser()

        self._models: Dict[str, Type[BaseModel]] = {}
        self._name_counter = 0

    def convert(self, data: Dict[str, Any], root_name: str = "RootModel") -> Type[BaseModel]:
        try:
            return self._parse_object(data, root_name)
        except Exception as e:
            raise RuntimeError("Error converting data", str(e))

    def get_models(self) -> Dict[str, Type[BaseModel]]:
        """
        Retorna um dicionário contendo todos os modelos Pydantic que foram gerados 
        durante o processamento dos dados.

        Returns:
            Dict[str, Type[BaseModel]]: Dicionário onde as chaves são nomes dos modelos e os valores são os tipos dos modelos Pydantic.
        """
        return self._models

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

    def _parse_object(self, obj: Dict[str, Any], name: str) -> Type[BaseModel]:
        fields = {}

        for key, value in obj.items():
            fields[key] = self._parse_field(key, value)

        return self._create_model(name, fields)

    def _parse_field(self, key: str, value: Any) -> Tuple[Any, Any]:
        """
        Analisa o valor de um campo e determina seu tipo e eventuais metadados, gerando
        o tipo adequado para o campo no modelo Pydantic.

        Args: 
        key (str): Nome do campo a ser analisado.
        value (Any): Valor do campo, usado para deduzir o tipo e metadados.

        Returns:
                Tuple[Any, Any]: Uma tupla contendo o tipo do campo e um objeto Field com metadados para o Pydantic.

        Raises:
                RuntimeError: Erro ocorrido durante o parsing do campo.
        """
        try:
            metadata = self.metadata_parser.parse(value)
            if metadata:
                return metadata

            description = f"Auto-generated field for {key}"

            if isinstance(value, dict):
                model_name = self._generate_name(key)
                nested_model = self._parse_object(value, model_name)
                return nested_model, ...

            if isinstance(value, list):
                if not value:
                    return List[Any], Field(description=description)

                first = value[0]

                if isinstance(first, dict):
                    model_name = self._generate_name(
                        inflector.singular_noun(key) or key
                    )
                    nested_model = self._parse_object(first, model_name)
                    return List[nested_model], ...

                item_type = self._resolve_type(first)
                return List[item_type], Field(description=description)

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


# python -m src.content_parse.pydantic_shema
# inflect==7.5.0