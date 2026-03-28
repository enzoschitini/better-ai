import os
from dotenv import load_dotenv

from src.agents.ultils.tool_response import ToolResponse
from src.agents.deep_research.toolkit import DeepResearch
from src.utils.unique_id_factory import IDGenerator
from src.agents.deep_research.config import DEFAULT_MODEL, PROMPT, LOCAL_MEMORY_DB

from agno.agent import Agent

from agno.models.groq import Groq
from agno.models.openai import OpenAIChat
from agno.models.google import Gemini

from agno.db.sqlite import SqliteDb
from agno.db.postgres import PostgresDb
from agno.memory.manager import MemoryManager

load_dotenv()

agent = Agent(
    # Settings
    id="deep_research",
    model=OpenAIChat(id=DEFAULT_MODEL), 
    instructions=PROMPT["instructions"],
    description=PROMPT["description"],
    markdown=True,
    stream=True,
    debug_level=True,

)

if __name__ == "__main__":
    from src.agents.ultils.run_agent import RunAgent

    runner = RunAgent(agent=agent)
    ASK = """
Quem tem mais chance de ganhar a copa de 2026?
"""
    #runner.process(ask="O que está sendo falado sobre a copa de 2026?", tool_responses=response_collector)
    runner.debug(ask=ASK)
    #runner.agent_os()

# python -m src.dev_tools.doc_class.agent