import json
import os

# Default output folder: src/deep_agents/data (independent of the current working directory)
DEFAULT_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
)


def manage_result_json(
    result: dict,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    filename: str = "agent_result.json",
) -> str:
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
