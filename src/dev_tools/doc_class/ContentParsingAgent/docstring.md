```python
import json
from dotenv import load_dotenv
from typing import Optional, Dict, Any

from agno.agent import Agent
from agno.models.groq import Groq
from agno.models.openai import OpenAIResponses

from src.content_parse.config import Config
from src.content_parse.pydantic_schema import JsonToPydantic, GeneratePydanticSchema

load_dotenv()

class ContentParsingAgent:
    """
    Agente responsável por processar dados de entrada e saída, gerar esquemas Pydantic a partir desses dados,
    e executar um modelo de linguagem configurável para processar o conteúdo conforme instruções fornecidas.

    Args:
    :param input_data (Dict[str, Any]): Dicionário contendo os dados de entrada a serem processados.
    :param output_data (Dict[str, Any]): Dicionário contendo os dados de saída esperados após o processamento.
    :param config_data (Optional[Dict[str, Any]]): Dicionário opcional com dados de configuração do agente. Default é None.

    Methods:
            get_schemas(): Retorna os schemas Pydantic gerados para input, output e configuração.
            run_agent(): Executa o agente com base no modelo configurado e retorna a resposta.
            format_response(raw_response): Formata a resposta bruta do agente em um dicionário estruturado com conteúdo e metadados.
    """
    def __init__(
        self,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        config_data: Optional[Dict[str, Any]] = None,
    ):
        self.input_data = input_data
        self.output_data = output_data
        self.config_data = config_data

        self._generate_schemas()

    def _generate_schemas(self):
        """
        Gera os schemas Pydantic para os dados de entrada, saída e configuração.
        Utiliza parseadores específicos para conversão dos dados brutos em modelos validados.

        Raises:
                RuntimeError: Caso ocorra algum erro na geração dos schemas.
        """
        try:
            parser = JsonToPydantic()
            converter = GeneratePydanticSchema()

            self.input_schema = parser.parse(self.input_data)
            self.output_schema = converter.convert(self.output_data, "OutputSchema")

            if self.config_data is not None:
                self.config_schema = parser.parse(self.config_data)
            else:
                self.config_schema = Config()

        except Exception as e:
            raise RuntimeError("Error generating schemas", str(e))    

    def _get_model(self):
        """
        Seleciona e retorna o modelo de linguagem apropriado com base no provedor configurado.

        Returns:
                Instância do modelo configurado conforme o provedor estabelecido na configuração.

        Raises:
                ValueError: Caso o provedor de modelo configurado não seja suportado.
        """
        if self.config_schema.model_provider.lower() == "openai":
            return OpenAIResponses(id=self.config_schema.model_id, temperature=0)
        elif self.config_schema.model_provider.lower() == "groq":
            return Groq(id=self.config_schema.model_id)
        else:
            raise ValueError(f"Unsupported model provider: {self.config_schema.model_provider}")

    def get_schemas(self):
        """
        Retorna os schemas Pydantic referentes aos dados de entrada, saída e configuração.

        Returns:
                dict: Dicionário contendo os schemas 'input', 'output' e 'config'.
        """
        return {
            "input": self.input_schema,
            "output": self.output_schema,
            "config": self.config_schema,
        }

    def run_agent(self):
        """
        Executa o agente utilizando o modelo configurado, instruções e descrição para processar os dados de entrada,
        e retorna a resposta gerada pelo modelo.

        Returns:
                Resposta gerada pelo agente após o processamento da entrada.

        Raises:
                RuntimeError: Caso ocorra algum erro durante a execução do agente.
        """
        try:
            agent = Agent(
                model=self._get_model(),
                instructions=self.config_schema.instructions,
                description=self.config_schema.description,
                debug_mode=self.config_schema.debug_mode,
                output_schema=self.output_schema,
            )

            response = agent.run(input=self.input_schema)
            return response
        except Exception as e:
            raise RuntimeError("Error running agent", str(e))    

    def format_response(self, raw_response):
        """
        Formata a resposta bruta obtida do agente em um dicionário estruturado, extraindo conteúdo,
        informações sobre o modelo utilizado e métricas relacionadas à execução.

        Args: 
        raw_response: Objeto de resposta bruta retornado pelo agente.

        Returns:
                dict: Conteúdo formatado em um dicionário estruturado pronto para uso ou publicação.

        Raises:
                RuntimeError: Caso ocorra algum erro durante a formatação da resposta.
        """
        try:
            content = raw_response.content.model_dump()
            metrics_dict = raw_response.metrics.__dict__
            model_metrics = metrics_dict["details"]["model"][0]

            response = {
                "content": content,
                "metadata": {
                    "model": {
                        "provider": model_metrics.provider.split(" ")[0],
                        "id": model_metrics.id
                    },
                    "tokens": {
                        "input_tokens": model_metrics.input_tokens,
                        "output_tokens": model_metrics.output_tokens,
                        "total_tokens": model_metrics.total_tokens,
                    },
                    "duration_s": round(metrics_dict.get("duration"), 2),
                }
            }

            return response

        except Exception as e:
            raise RuntimeError("Error formatting response", str(e))
```