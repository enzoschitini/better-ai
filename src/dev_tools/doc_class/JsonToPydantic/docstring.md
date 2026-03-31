```python
from typing import Any, Dict, List, Type, Tuple
from pydantic import BaseModel, Field, create_model
from typing import Any, Dict, Type
import inflect

inflector = inflect.engine()

class JsonToPydantic:
    """
    Classe para converter um dicionário JSON em um modelo Pydantic dinâmico, inferindo os tipos de dados dos campos.

    Args:
        :param model_name (str): Nome do modelo Pydantic dinâmico que será criado. Default é "DynamicModel".

    Methods:
            generate_post(topic): Explica o metodo em uma frase
    """

    def __init__(self, model_name: str = "DynamicModel"):
        self.model_name = model_name

    def _infer_type(self, value: Any) -> Type:
        """
        Determina o tipo Python adequado com base no valor fornecido, facilitando a criação dinâmica de modelos.

        Args:
            value (Any): Valor do qual se deseja inferir o tipo.

        Returns:
                Type: Tipo Python inferido para o valor.
        
        Raises:
                RuntimeError: Caso ocorra um erro durante a inferência do tipo.
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
        Cria dinamicamente um modelo Pydantic a partir de um dicionário, utilizando tipos inferidos dos valores.

        Args:
            data (Dict[str, Any]): Dicionário contendo os dados que definirão os campos do modelo.

        Returns:
                Type[BaseModel]: Modelo Pydantic criado dinamicamente com os campos e tipos inferidos.
        
        Raises:
                RuntimeError: Caso ocorra um erro durante a construção do modelo.
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
        Constrói um modelo Pydantic dinâmico e instancia-o com os dados fornecidos.

        Args:
            data (Dict[str, Any]): Dicionário contendo os dados para popular o modelo.

        Returns:
                BaseModel: Instância do modelo Pydantic com os dados validados e estruturados.
        
        Raises:
                RuntimeError: Caso ocorra um erro durante o parsing dos dados.
        """
        try:
            model = self.build_model(data)
            return model(**data)
        except Exception as e:
            raise RuntimeError("Error parsing data", str(e))
```