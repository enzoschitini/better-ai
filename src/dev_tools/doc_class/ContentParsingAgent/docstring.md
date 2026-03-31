```python
import json
from dotenv import load_dotenv
from typing import Optional, Dict, Any

from agno.agent import Agent
from agno.models.groq import Groq
from agno.models.openai import OpenAIResponses

from src.text_parse.config import Config
from src.text_parse.pydantic_shema import JsonToPydantic, GeneratePydanticSchema

load_dotenv()

class ContentParsingAgent:
    """
    Classe responsável por inicializar e executar um agente de parsing de conteúdo que utiliza esquemas Pydantic
    para validar e converter dados de entrada, saída e configuração. Gerencia a seleção do modelo adequado
    e formata a resposta do agente para incluir métricas e metadados.

    Args: 
    :param input_data (Dict[str, Any]): Dicionário contendo os dados de entrada a serem processados pelo agente.
    :param output_data (Dict[str, Any]): Dicionário contendo o esquema de dados de saída esperado pelo agente.
    :param config_data (Optional[Dict[str, Any]]): Dicionário opcional contendo configurações adicionais para o agente. Default é None.

    Methods:
            generate_post(topic): Explica o metodo em uma frase
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
        Gera esquemas Pydantic para os dados de entrada, saída e configuração com base nos dados fornecidos,
        permitindo validação e conversão estruturada.

        Raises:
                RuntimeError: Se ocorrer um erro durante a geração dos esquemas, uma exceção é lançada com detalhes do erro.
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
        Seleciona e instancia o modelo apropriado baseado na configuração do provider especificado
        no esquema de configuração.

        Returns:
                OpenAIResponses ou Groq: Instância do modelo configurado conforme o provider selecionado.

        Raises:
                ValueError: Se o provider do modelo for desconhecido ou não suportado.
        """
        if self.config_schema.model_provider.lower() == "openai":
            return OpenAIResponses(id=self.config_schema.model_id, temperature=0)
        elif self.config_schema.model_provider.lower() == "groq":
            return Groq(id=self.config_schema.model_id)
        else:
            raise ValueError(f"Unsupported model provider: {self.config_schema.model_provider}")

    def get_schemas(self):
        """
        Retorna os esquemas atualmente gerados para entrada, saída e configuração.

        Returns:
                dict: Dicionário contendo os esquemas 'input', 'output' e 'config'.
        """
        return {
            "input": self.input_schema,
            "output": self.output_schema,
            "config": self.config_schema,
        }

    def run_agent(self):
        """
        Executa o agente configurado com os modelos e instruções especificados, utilizando os dados de entrada
        validados pelo esquema correspondente, e retorna a resposta gerada pelo agente.

        Returns:
                Conteúdo da resposta gerada pelo agente.

        Raises:
                RuntimeError: Se ocorrer um erro durante a execução do agente, uma exceção é lançada com detalhes do erro.
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
        Formata a resposta crua do agente para incluir o conteúdo modelado e metadados relevantes,
        como informações do modelo e métricas de uso, retornando um dicionário estruturado.

        Args: 
        raw_response: Resposta bruta obtida após a execução do agente, contendo conteúdo e métricas.

        Returns:
                dict: Estrutura contendo o conteúdo formatado e metadados incluindo informações do modelo e métricas.

        Raises:
                RuntimeError: Se ocorrer um erro durante a formatação da resposta, uma exceção é lançada com detalhes do erro.
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
                    "metrics": {
                        "input_tokens": model_metrics.input_tokens,
                        "output_tokens": model_metrics.output_tokens,
                        "total_tokens": model_metrics.total_tokens,
                    },
                    "duration": round(metrics_dict.get("duration"), 2),
                }
            }

            print(json.dumps(response, indent=2))
            return response

        except Exception as e:
            raise RuntimeError("Error formatting response", str(e))

# python -m src.text_parse.content_parsing_agent
```