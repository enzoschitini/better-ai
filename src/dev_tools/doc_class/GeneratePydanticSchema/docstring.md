```python
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
```