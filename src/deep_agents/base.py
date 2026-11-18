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


def extract_response_text(result: dict) -> str:
    """Return the text of the last message in the agent result."""
    final_message = result["messages"][-1]
    # `.text` is a property in current langchain-core (a str subclass that is also
    # callable for backwards compat) — never call it, just use it as a string.
    response = getattr(final_message, "text", None) or final_message.content
    return str(response)


def chat_loop() -> None:
    """Interactive terminal chat. Keeps the conversation history between turns.

    Commands: /exit (or /quit) to leave, /clear to reset the conversation.
    The full JSON of the latest turn is saved to agent_result.json.
    """
    print("Deep Agent chat — digite /exit para sair, /clear para limpar o histórico.\n")
    messages: list = []

    while True:
        try:
            user_input = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté logo!")
            break

        if not user_input:
            continue
        if user_input.lower() in {"/exit", "/quit", "exit", "quit"}:
            print("Até logo!")
            break
        if user_input.lower() == "/clear":
            messages = []
            print("Histórico limpo.\n")
            continue

        messages.append({"role": "user", "content": user_input})
        try:
            result = agent.invoke({"messages": messages})
        except Exception as e:
            messages.pop()  # drop the failed turn so the history stays consistent
            print(f"\n[erro] {e}\n")
            continue

        # The returned messages already contain the whole history + the new reply
        messages = result["messages"]
        manage_result_json(result)

        print(f"\nAgente: {extract_response_text(result)}\n")


if __name__ == "__main__":
    chat_loop()

# python -m src.deep_agents.base