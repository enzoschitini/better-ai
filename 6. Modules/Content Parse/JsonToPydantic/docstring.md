```python
from typing import Any, Dict, Type
from pydantic import BaseModel, create_model

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
```