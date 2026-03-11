import json
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from src.agents.agent_flow.format_response import FormatAgentResponse
from src.agents.agent_flow.agent_toolkit import ToolResponse, DeepResearch
from src.agents.deep_research.config import PROMPT

from agno.agent import Agent
from agno.os import AgentOS

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
)

if __name__ == "__main__":
    agent_os = AgentOS(
        id="my-first-os",
        description="My first AgentOS",
        agents=[agent],
    )

    app = agent_os.get_app()
    agent_os.serve(app=app)


"""
ASK = "O que está sendo falado sobre a copa do mundo de 2026?"
#agent.print_response(ASK)

class AgentInput(BaseModel):
    text: str

response = agent.run(
    input=AgentInput(text=ASK)
)

formatter = FormatAgentResponse(response)
super_json = formatter.format()
formatter.save_json(super_json, "src/agents/agent_flow/agent_response.json")

print(f"\n\n{json.dumps(super_json, indent=2)}\n\n")

print(f"Metadata: {response_collector.get_metadata()}")
print(f"Response: {response.content}")

if __name__ == "__main__":
    agent_os = AgentOS(
        id="my-first-os",
        description="My first AgentOS",
        agents=[agent],
    )

    app = agent_os.get_app()
    agent_os.serve(app=app)

"""



# python -m src.agents.deep_research.agent