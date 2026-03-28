from dotenv import load_dotenv

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from src.agents.deep_research.config import DEFAULT_MODEL
from src.dev_tools.doc_class.config import (
    AgentConfig,
    GenereteDocStringConfig,
    GenereteDocClassConfig
)

load_dotenv()


class GenereteDoc:
    def __init__(self):
        self.config = AgentConfig()

    def _get_prompt_config(self):
        if self.about == "docstring":
            prompt_config = GenereteDocStringConfig()

        elif self.about == "class":
            prompt_config = GenereteDocClassConfig()

        else:
            raise ValueError("about must be 'docstring' or 'class'")

        self.instructions = prompt_config.instructions
        self.description = prompt_config.description

    def _create_agent(self):
        return Agent(
            id="deep_research",
            model=OpenAIChat(id=DEFAULT_MODEL),
            instructions=self.instructions,
            description=self.description,
            markdown=True,
            debug_level=True,
        )

    def _parse_result(self, result):
        if hasattr(result, "output"):
            return result.output

        if hasattr(result, "content"):
            return result.content

        return str(result)

    def generate_doc_string(self, input: str):
        try:
            self.about = "docstring"
            self._get_prompt_config()

            agent = self._create_agent()
            result = agent.run(input=input)

            return self._parse_result(result)

        except Exception as e:
            raise RuntimeError("Erro: GenereteDoc.generate_doc_string", str(e))

    def generate_doc_class(self, input: str):
        try:
            self.about = "class"
            self._get_prompt_config()

            agent = self._create_agent()
            result = agent.run(input=input)

            return self._parse_result(result)

        except Exception as e:
            raise RuntimeError("Erro: GenereteDoc.generate_doc_class", str(e))


if __name__ == "__main__":
    gen = GenereteDoc()
    result = gen.generate_doc_class("Oi")

    print(result)  # agora é string

# python -m src.dev_tools.doc_class.agent