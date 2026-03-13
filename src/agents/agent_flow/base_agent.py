from dotenv import load_dotenv
from typing import Any, List

from agno.agent import Agent
from agno.os import AgentOS
from agno.tools import Toolkit

from agno.db.sqlite import SqliteDb
from agno.memory.manager import MemoryManager

from agno.models.groq import Groq
from agno.models.openai import OpenAIChat

from src.agents.agent_flow.config import PROMPT, CONTEXT, BASE_PATH

load_dotenv()

class ToolResponse:
    def __init__(self, metadata=None):
        self.metadata = metadata or {}

    def add_metadata(self, tool_name: str, payload: dict):
        self.metadata[tool_name] = payload
    
    def get_metadata(self):
        return self.metadata

class VectorStoreRetriver(Toolkit):
    """
    VectorStoreRetriver is a toolkit for (RAG) retrieval augmented generation. 

    Args:
        enable_context_generation (bool): Enable generate context functionality. Default is True.
        all (bool): Enable all tools. Overrides individual flags when True. Default is False.
    """

    def __init__(
        self,
        response_collector: Any,
        enable_context_generation: bool = True,
        all: bool = False,
        **kwargs,
    ):
        self.response_collector = response_collector
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
            self.response_collector.add_metadata(
                tool_name="context_generation",
                payload={
                    "context": len(context)
                }
            )

        except Exception as e:
            return f"Failed to generate context: {str(e)}"

        return context

# Setup your database
db = SqliteDb(db_file=f"{BASE_PATH}agno.db")
tool_respose = ToolResponse()

agent = Agent(
    # Menage sessions and users
    session_id="session_4",
    user_id="user_2",

    # Models: OpenAIChat(id="gpt-4.1-mini"), Groq(id="llama-3.3-70b-versatile"),
    model=Groq(id="llama-3.3-70b-versatile", temperature=0.8), 

    instructions=PROMPT["instructions"],
    description=PROMPT["description"],
    metadata={
        "conversation_title": "title"
    },

    #debug_mode=True,
    stream=False,
    #markdown=True,

    # Memory
    db=db,
    add_history_to_context=True,
    num_history_runs=10,
    enable_user_memories=True,
    add_memories_to_context=True,

    memory_manager=MemoryManager(
        db=db,
        model=OpenAIChat(id="gpt-4.1-mini"),
        additional_instructions=PROMPT["memory_manager_instructions"]
    ),
    enable_agentic_memory=True,

    #session_summary_manager=
    tools=[VectorStoreRetriver(response_collector=tool_respose)],
)

if __name__ == "__main__":
    from src.agents.ultils.run_agent import RunAgent

    runner = RunAgent(agent=agent)
    runner.agent_os()

    # python -m src.agents.agent_flow.base_agent













