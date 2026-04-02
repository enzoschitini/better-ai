import json
from dotenv import load_dotenv
from typing import Optional, Dict, Any

from agno.agent import Agent
from agno.models.groq import Groq
from agno.models.openai import OpenAIResponses

from src.text_parse.config import Config
from src.text_parse.pydantic_schema import JsonToPydantic, GeneratePydanticSchema

load_dotenv()

class ContentParsingAgent:
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
        if self.config_schema.model_provider.lower() == "openai":
            return OpenAIResponses(id=self.config_schema.model_id, temperature=0)
        elif self.config_schema.model_provider.lower() == "groq":
            return Groq(id=self.config_schema.model_id)
        else:
            raise ValueError(f"Unsupported model provider: {self.config_schema.model_provider}")

    def get_schemas(self):
        return {
            "input": self.input_schema,
            "output": self.output_schema,
            "config": self.config_schema,
        }

    def run_agent(self):
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
                    "duration_s": round(metrics_dict.get("duration_s"), 2),
                }
            }

            return response

        except Exception as e:
            raise RuntimeError("Error formatting response", str(e))

# python -m src.text_parse.content_parsing_agent