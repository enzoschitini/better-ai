import json
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from src.agents.agent_flow.config import CONTEXT

from agno.agent import Agent
from agno.os import AgentOS

from agno.models.groq import Groq
from agno.models.openai import OpenAIChat

load_dotenv()

prompt = {
    "instructions": """
Você é um analista e tem diferentes clientes. Lembre-se de cada cliente, suas informações e preferências.
""",

    "description": """
Você é um agente de IA RAG. Capaz de buscar por informações em uma vector store.
""",

    "memory_manager_instructions": """
Não armazene CPF e senhas dos usuários
"""
}

class ToolResponse:
    def __init__(self, metadata=None):
        self.metadata = metadata or {}

    def add_metadata(self, tool_name: str, payload: dict):
        self.metadata[tool_name] = payload
    
    def get_metadata(self):
        return self.metadata



from typing import Any, List
from agno.tools import Toolkit

class VectorStoreRetriver(Toolkit):
    """
    VectorStoreRetriver is a toolkit for (RAG) retrieval augmented generation. 

    Args:
        enable_context_generation (bool): Enable generate context functionality. Default is True.
        all (bool): Enable all tools. Overrides individual flags when True. Default is False.
    """

    def __init__(
        self,
        enable_context_generation: bool = True,
        all: bool = False,
        **kwargs,
    ):
        tools: List[Any] = []

        if all or enable_context_generation:
            tools.append(self.context_generation)

        super().__init__(name="vector_store_tools", tools=tools, **kwargs)

    def context_generation(self, query: str) -> str:
        """
        Generate contextual information based on a user query.
        """

        try:
            context = CONTEXT

        except Exception as e:
            return f"Failed to generate context: {str(e)}"

        return context

response_collector = ToolResponse()
context = VectorStoreRetriver()

agent = Agent(
    # Models: OpenAIChat(id="gpt-4.1-mini"), Groq(id="llama-3.3-70b-versatile"),
    model=OpenAIChat(id="gpt-4.1-mini"), 

    instructions=prompt["instructions"],
    description=prompt["description"],
    debug_level=True,
    tools=[context],
)

ASK = "Resuma os documentos da base"
#agent.print_response(ASK)

if __name__ == "__main__":
    agent_os = AgentOS(
        id="my-first-os",
        description="My first AgentOS",
        agents=[agent],
    )

    app = agent_os.get_app()
    agent_os.serve(app=app)

# python -m src.agents.agent_flow.rag_agent
