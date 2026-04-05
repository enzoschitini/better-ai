```python
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
```