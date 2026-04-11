import os
from dotenv import load_dotenv

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from agno.memory.manager import MemoryManager

from src.agents.ultils.database import Database
from src.agents.ultils.tool_response import ToolResponse
from src.agents.rag_agent.toolkit import RetrievalAugmentedGeneration
from src.agents.rag_agent.config import DEFAULT_MODEL, PROMPT

load_dotenv()

DATABASE = Database()
TOOL_RESPONSER = ToolResponse()
USE_REASONING = False

reasoning_config = (
    {
        "reasoning": True,
        "reasoning_model": OpenAIChat(
            id=DEFAULT_MODEL,
            instructions="""
            Você é responsável por decidir como resolver a tarefa.
            Lembre-se, você tem tools, use quando necessario.
            """
        ),
        "reasoning_max_steps": 5
    }
    if USE_REASONING else {}
)

agent = Agent(
    id="rag_agent",

    # Settings
    model=OpenAIChat(
        id=DEFAULT_MODEL,
        temperature=0.8,
        max_completion_tokens=800,
        top_p=0.9,
        seed=42,
        frequency_penalty=0.2,
        logprobs=True,
        top_logprobs=5,
        strict_output=True,
    ), 

    instructions=PROMPT["instructions"],
    description=PROMPT["description"],
    markdown=True,
    stream=True,
    debug_level=True,

    # Reasoning
    **reasoning_config,

    # Chat Memory
    db=DATABASE,
    add_history_to_context=True,
    num_history_runs=10,
    enable_user_memories=True,
    add_memories_to_context=True,

    # Agentic Memory
    memory_manager=MemoryManager(
        db=DATABASE,
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
Quais arquivos estão na base?
"""
    #runner.run_agent(ask=ASK, tool_responses=TOOL_RESPONSER)
    runner.debug(ask=ASK)
    #runner.agent_os()

    print(json.dumps(TOOL_RESPONSER.get_metadata(), indent=4))

"""
    reasoning=True,
    reasoning_model=OpenAIChat(id=DEFAULT_MODEL),
    reasoning_max_steps=5,
"""
# python -m src.agents.rag_agent.agent