import os
from dotenv import load_dotenv

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from src.agents.ultils.tool_response import ToolResponse
from src.agents.rag.toolkit import RetrievalAugmentedGeneration
from src.agents.sheet_analyzer.config import DEFAULT_MODEL, PROMPT, LOCAL_MEMORY_DB

load_dotenv()

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

    # Toolkit
    tools=[
        RetrievalAugmentedGeneration(TOOL_RESPONSER=TOOL_RESPONSER)
    ],
)

if __name__ == "__main__":
    from src.agents.ultils.run_agent import RunAgent

    runner = RunAgent(agent=agent)
    ASK = """
Gere um grafico de barras da quantidade de pessoas por genero
"""
    #runner.process(ask=ASK, tool_responses=response_collector)
    runner.debug(ask=ASK)
    #runner.agent_os()

# python -m src.agents.rag.agent