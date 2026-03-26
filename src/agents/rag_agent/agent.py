import os
from dotenv import load_dotenv

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from agno.db.sqlite import SqliteDb
from agno.db.postgres import PostgresDb
from agno.memory.manager import MemoryManager

from src.agents.ultils.tool_response import ToolResponse
from src.agents.rag_agent.toolkit import RetrievalAugmentedGeneration
from src.agents.rag_agent.config import DEFAULT_MODEL, PROMPT, LOCAL_MEMORY_DB

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

        return PostgresDb(
            db_url=SUPABASE_DB_URL,

            session_table="sessions",
            memory_table="memories",
            metrics_table="metrics",
            eval_table="eval_runs",
            knowledge_table="knowledge",
            culture_table="culture",
            traces_table="traces",
            spans_table="spans",
            versions_table="schema_versions",
            components_table="components",
            component_configs_table="component_configs",
            component_links_table="component_links",
            learnings_table="learnings",
            schedules_table="schedules",
            schedule_runs_table="schedule_runs",
            approvals_table="approvals",
        )

    @staticmethod
    def local_database():
        return SqliteDb(
            db_file=LOCAL_MEMORY_DB,

            session_table="sessions",
            memory_table="memories",
            metrics_table="metrics",
            eval_table="eval_runs",
            knowledge_table="knowledge",
            culture_table="culture",
            traces_table="traces",
            spans_table="spans",
            versions_table="schema_versions",
            components_table="components",
            component_configs_table="component_configs",
            component_links_table="component_links",
            learnings_table="learnings",
            schedules_table="schedules",
            schedule_runs_table="schedule_runs",
            approvals_table="approvals",
        )

db = Database(local=True)
TOOL_RESPONSER = ToolResponse()

agent = Agent(
    id="rag_agent",

    # Settings
    model=OpenAIChat(id=DEFAULT_MODEL), 
    instructions=PROMPT["instructions"],
    description=PROMPT["description"],
    markdown=True,
    stream=True,
    debug_level=True,

    # Reasoning

    # Chat Memory
    db=db,
    add_history_to_context=True,
    num_history_runs=10,
    enable_user_memories=True,
    add_memories_to_context=True,

    # Agentic Memory
    memory_manager=MemoryManager(
        db=db,
        model=OpenAIChat(id=DEFAULT_MODEL),
        additional_instructions=PROMPT["memory_manager_instructions"]
    ),
    enable_agentic_memory=True,

    # Toolkit
    tools=[
        RetrievalAugmentedGeneration(
            filter_search={
                "file_id": ["candidatura", "tenerezza", "cucinare"]
            },
            TOOL_RESPONSER=TOOL_RESPONSER
        )
    ],
)

if __name__ == "__main__":
    import json
    from src.agents.ultils.run_agent import RunAgent

    runner = RunAgent(agent=agent)
    ASK = """
Oi
"""
    #runner.run_agent(ask=ASK, tool_responses=TOOL_RESPONSER)
    #runner.debug(ask=ASK)
    runner.agent_os()

    print(json.dumps(TOOL_RESPONSER.get_metadata(), indent=4))

"""
    reasoning=True,
    reasoning_model=OpenAIChat(id=DEFAULT_MODEL),
    reasoning_max_steps=5,
"""
# python -m src.agents.rag_agent.agent