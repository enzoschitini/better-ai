from dotenv import load_dotenv

from src.agents.agent_flow.agent_toolkit import ToolResponse, DeepResearch
from src.agents.deep_research.config import PROMPT

from agno.agent import Agent

from agno.models.groq import Groq
from agno.models.openai import OpenAIChat

from agno.db.sqlite import SqliteDb
from agno.memory.manager import MemoryManager

load_dotenv()

# Setup your database
BASE_PATH = "src/agents/deep_research/"
db = SqliteDb(db_file=f"{BASE_PATH}agno.db")

response_collector = ToolResponse()

agent = Agent(
    id="laura94",
    model=OpenAIChat(id="gpt-4.1-mini"), 
    instructions=PROMPT["instructions"],
    description=PROMPT["description"],
    debug_level=True,
    metadata={
        "conversation_title": "title"
    },

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

    tools=[DeepResearch(response_collector)],

    # salvar execução
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
    #runner.process(response_collector=response_collector, ask="Olá")
    runner.agent_os()



# python -m src.agents.deep_research.agent