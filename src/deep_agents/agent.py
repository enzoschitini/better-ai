from dotenv import load_dotenv
from src.deep_agents.model.llm_gateway import LLMGateway
from src.deep_agents.model.model_config import ModelConfig

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

# Model configuration — the gateway applies per-provider rules (renamed/dropped params)
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

agent = gateway.agent(
    tools=[internet_search],
    system_prompt=research_instructions,
)

# python -m src.deep_agents.looping