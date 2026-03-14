from dotenv import load_dotenv

from src.agents.ultils.tool_response import ToolResponse
from src.agents.deep_research.toolkit import DeepResearch
from src.agents.deep_research.config import PROMPT, LOCAL_MEMORY_DB

from agno.agent import Agent

from agno.models.groq import Groq
from agno.models.openai import OpenAIChat

from agno.db.sqlite import SqliteDb
from agno.memory.manager import MemoryManager

load_dotenv()

db = SqliteDb(db_file=LOCAL_MEMORY_DB)

response_collector = ToolResponse()

agent = Agent(
    id="deep_research",
    metadata={
        "conversation_title": "title"
    },

    # Settings
    model=OpenAIChat(id="gpt-4.1-mini"), 
    instructions=PROMPT["instructions"],
    description=PROMPT["description"],
    debug_level=True,

    # Chat Memory
    db=db,
    add_history_to_context=True,
    num_history_runs=10,
    enable_user_memories=True,
    add_memories_to_context=True,

    # Agentic Memory
    memory_manager=MemoryManager(
        db=db,
        model=OpenAIChat(id="gpt-4.1-mini"),
        additional_instructions=PROMPT["memory_manager_instructions"]
    ),
    enable_agentic_memory=True,

    # Toolkit
    tools=[DeepResearch(response_collector)],

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
    runner.process(ask="O que está sendo falado sobre a copa de 2026?", tool_responses=response_collector)
    #runner.agent_os()

# python -m src.agents.deep_research.agent