import sys
from pathlib import Path

# Permite rodar direto (botão Play / `python arquivo.py`): coloca a raiz do repo no sys.path.
_RAIZ = Path(__file__).resolve().parents[2]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

from deepagents import create_deep_agent  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from src.deep_agents.model.llm_gateway import LLMGateway  # noqa: E402
from src.deep_agents.model.model_config import ModelConfig  # noqa: E402

# Load environment variables from a .env file
load_dotenv()

# OpenAI's built-in web search — no extra install or API key needed
internet_search = {"type": "web_search"}

# System prompt to steer the agent to be an expert researcher
research_instructions = """You are an expert researcher. Your job is to conduct thorough research and then write a polished report.

You have access to an internet search tool as your primary means of gathering information.

## `internet_search`

Use this to run an internet search for a given query. You can specify the max number of results to return, the topic, and whether raw content should be included.
"""

# Model only: the gateway applies per-provider rules (renamed/dropped params)
# and collects per-call metrics (tokens, latency, tool runs) in gateway.history.
gateway = LLMGateway(
    ModelConfig(
        provider="openai",
        model_id="gpt-6.1-sol",
        timeout=120,
        max_retries=2,
        # temperature=..., max_tokens=..., extra={...}  # optional controls
    )
)

# The agent itself is created here, receiving the model configured by the gateway.
agent = create_deep_agent(
    model=gateway.build(),
    tools=[internet_search],
    system_prompt=research_instructions,
)

# python -m src.deep_agents.looping