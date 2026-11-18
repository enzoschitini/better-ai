import os
import json

from dotenv import load_dotenv
from deepagents import create_deep_agent

# Load environment variables from a .env file
load_dotenv()

PATH = "src/deep_agents"

# OpenAI's built-in web search — no extra install or API key needed
internet_search = {"type": "web_search"}

# System prompt to steer the agent to be an expert researcher
research_instructions = """You are an expert researcher. Your job is to conduct thorough research and then write a polished report.

You have access to an internet search tool as your primary means of gathering information.

## `internet_search`

Use this to run an internet search for a given query. You can specify the max number of results to return, the topic, and whether raw content should be included.
"""

agent = create_deep_agent(
    model="openai:gpt-6.1-sol",
    tools=[internet_search],
    system_prompt=research_instructions,
)

def manage_result_json(result: dict, output_dir: str = PATH, filename: str = "agent_result.json") -> str:
    """Serialize the full agent result to JSON, save it to disk (UTF-8) and return the JSON string.

    `result["messages"]` holds LangChain message objects, which are not JSON
    serializable by default, so they are converted via `.model_dump()`;
    `default=str` is a fallback for any other non-serializable value.
    """
    messages = [
        m.model_dump() if hasattr(m, "model_dump") else m
        for m in result.get("messages", [])
    ]
    json_result = json.dumps(
        {**result, "messages": messages},
        indent=2,
        default=str,
        ensure_ascii=False,
    )

    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, filename)
    # Explicit UTF-8: Windows defaults to cp1252 and fails on characters like "↓"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(json_result)

    return json_result


result = agent.invoke({"messages": [{"role": "user", "content": "Che cos'è langgraph?"}]})
json_result = manage_result_json(result)

final_message = result["messages"][-1]
response = getattr(final_message, "text", None) or final_message.content
if callable(response):  # `.text` is a method on older langchain-core versions
    response = response()

# Print the agent's response
print(json_result)
print("\nAgent's Response:\n")
print(response)

# python -m src.deep_agents.base