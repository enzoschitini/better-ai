import os
from dotenv import load_dotenv

from src.agents.ultils.tool_response import ToolResponse
from src.agents.deep_research.toolkit import DeepResearch
from src.utils.unique_id_factory import IDGenerator
from src.agents.deep_research.config import DEFAULT_MODEL, PROMPT, LOCAL_MEMORY_DB

from agno.agent import Agent

from agno.models.groq import Groq
from agno.models.openai import OpenAIChat

from agno.db.sqlite import SqliteDb
from agno.db.postgres import PostgresDb
from agno.memory.manager import MemoryManager

load_dotenv()

class Database:
    def __new__(cls, local: bool = False):
        if local:
            return cls.local_database()
        return cls.supabase()

    @staticmethod
    def supabase():
        SUPABASE_PROJECT_HOST = os.getenv("SUPABASE_PROJECT_HOST")
        SUPABASE_DATABASE_PASSWORD = os.getenv("SUPABASE_DATABASE_PASSWORD")

        SUPABASE_DB_URL = (
            f"postgresql://postgres:{SUPABASE_DATABASE_PASSWORD}@db.{SUPABASE_PROJECT_HOST}:5432/postgres"
        )

        return PostgresDb(db_url=SUPABASE_DB_URL)

    @staticmethod
    def local_database():
        return SqliteDb(db_file=LOCAL_MEMORY_DB)

db = Database()
response_collector = ToolResponse()

agent = Agent(
    id="deep_research",
    metadata={
        "conversation_title": "title"
    },

    # Settings
    model=OpenAIChat(id=DEFAULT_MODEL), 
    instructions=PROMPT["instructions"],
    description=PROMPT["description"],
    markdown=True,
    stream=True,
    debug_level=True,

    # Chat Memory
    db=db,
    add_history_to_context=True,
    num_history_runs=10,
    enable_user_memories=True,
    add_memories_to_context=True,

    # Reasoning
    reasoning=True,
    reasoning_model="openai:gpt-4.1-mini",
    reasoning_max_steps=5,

    # Agentic Memory
    memory_manager=MemoryManager(
        db=db,
        model=OpenAIChat(id=DEFAULT_MODEL),
        additional_instructions=PROMPT["memory_manager_instructions"]
    ),
    enable_agentic_memory=True,

    # Toolkit
    tools=[DeepResearch(response_collector=response_collector)],

    # Save Traces
    store_history_messages=True,
    store_tool_messages=True,
    store_events=True,
    stream_events=True,
)

if __name__ == "__main__":
    from src.agents.ultils.run_agent import RunAgent

    runner = RunAgent(
        agent=agent
    )
    #runner.process(ask="O que está sendo falado sobre a copa de 2026?", tool_responses=response_collector)
    #runner.debug(ask="Crie um post cativante falando sobre a guerra atual")
    runner.agent_os()

# python -m src.agents.deep_research.agent