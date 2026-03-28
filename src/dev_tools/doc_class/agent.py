import os
from dotenv import load_dotenv

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from src.agents.deep_research.config import DEFAULT_MODEL, PROMPT, LOCAL_MEMORY_DB
from src.dev_tools.doc_class.config import AgentConfig, GenereteDocStringConfig, GenereteDocClassConfig


load_dotenv()

class GenereteDoc:
    def __init__(self):
        self.config = AgentConfig()

    def _get_prompt_config(self):
        try:
            if self.about == "docstring":
                prompt_config = GenereteDocStringConfig()
                self.instructions = prompt_config.instructions
                self.description = prompt_config.description

            elif self.about == "class":
                prompt_config = GenereteDocClassConfig()
                self.instructions = prompt_config.instructions
                self.description = prompt_config.description
            
            else:
                raise ValueError("Erro: GenereteDoc._get_prompt_config. about is not [docstring, class]", str(e))

        except Exception as e:
            raise RuntimeError("Erro: GenereteDoc._get_prompt_config", str(e))

    def _create_agent(self):
        try:
            agent = Agent(
                # Settings
                id="deep_research",
                model=OpenAIChat(id=DEFAULT_MODEL), 
                instructions=self.instructions,
                description=self.description,
                markdown=True,
                #stream=True,
                debug_level=True,

            )

            self.agent = agent

            return self.agent

        except Exception as e:
            raise RuntimeError("Erro: GenereteDoc.generate_doc_string", str(e))

    def generate_doc_string(self, input: str):
        try:
            self.about = "docstring"
            self._get_prompt_config()
            self._create_agent()
            doc = self.agent.run(input=input)

            return doc

        except Exception as e:
            raise RuntimeError("Erro: GenereteDoc.generate_doc_string", str(e))

    def generate_doc_class(self, input: str):
        try:
            self.about = "class"
            self._get_prompt_config()
            self._create_agent()

            doc = self.agent.run(input=input)

            return doc

        except Exception as e:
            raise RuntimeError("Erro: GenereteDoc.generate_doc_class", str(e))


if __name__ == "__main__":
    import json
    
    gen = GenereteDoc()
    result = gen.generate_doc_class("Oi")

    print(result.content)

# python -m src.dev_tools.doc_class.agent