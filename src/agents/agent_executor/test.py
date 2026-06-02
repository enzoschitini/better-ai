import argparse
import json
from datetime import datetime
from typing import Any, Dict, List

from dotenv import load_dotenv

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools import Toolkit

from src.agents.agent_executor import AgentExecutor

load_dotenv()


class SimpleToolkit(Toolkit):
    """Small toolkit used to validate tool collection in executor flows."""

    def __init__(self, tool_responser: Any = None, **kwargs):
        self.tool_responser = tool_responser
        tools: List[Any] = [self.get_current_datetime, self.shout_text]
        super().__init__(name="simple_test_toolkit", tools=tools, **kwargs)

    def _collect(self, tool_name: str, payload: Dict[str, Any]) -> None:
        if self.tool_responser:
            self.tool_responser.add_metadata(tool_name=tool_name, payload=payload)

    def get_current_datetime(self, _: str = "") -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._collect("get_current_datetime", {"datetime": now})
        return now

    def shout_text(self, text: str) -> str:
        if not text or not text.strip():
            return "A valid text is required."

        output = text.upper()
        self._collect("shout_text", {"input": text, "output": output})
        return output


class SimpleTestAgent:
    """Simple agent contract compatible with AgentExecutor.from_agent_class."""

    def create_agent(self, metadata: dict, tool_context: Any) -> Agent:
        if "session_id" not in metadata:
            raise ValueError("metadata must contain 'session_id'")
        if "user_id" not in metadata:
            raise ValueError("metadata must contain 'user_id'")

        return Agent(
            id="simple_test_agent",
            session_id=metadata["session_id"],
            user_id=metadata["user_id"],
            model=OpenAIChat(id="gpt-4o-mini"),
            instructions=[
                "You are a simple testing agent.",
                "Use tools when they are helpful to answer user requests.",
                "Keep responses concise.",
            ],
            markdown=True,
            stream=True,
            tools=[SimpleToolkit(tool_responser=tool_context.tool_responser)],
        )


def build_executor(session_id: str | None = None, user_id: str | None = None) -> AgentExecutor:
    return AgentExecutor.from_agent_class(
        agent_class=SimpleTestAgent,
        params={},
        session_id=session_id,
        user_id=user_id,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple test for AgentExecutor")
    parser.add_argument(
        "--mode",
        choices=["json", "cli", "agentos", "api-direct", "api-stream"],
        default="cli",
        help="Execution mode",
    )
    parser.add_argument("--ask", default="Tell me the current datetime.", help="Input prompt")
    parser.add_argument("--session-id", default=None, help="Optional session id")
    parser.add_argument("--user-id", default=None, help="Optional user id")
    parser.add_argument("--host", default="localhost", help="Host for AgentOS/API")
    parser.add_argument("--port", type=int, default=7777, help="Port for AgentOS/API")
    parser.add_argument("--agent-id", default="simple_test_agent", help="AgentOS agent id for API mode")
    parser.add_argument(
        "--output",
        default="process_output.json",
        help="Output file path used in json mode",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    executor = build_executor(session_id=args.session_id, user_id=args.user_id)

    if args.mode == "json":
        response = executor.run_json(
            ask=args.ask,
            output_path=args.output,
            include_tool_metadata=True,
            clear_tool_metadata=True,
        )
        print(json.dumps(response, indent=2, ensure_ascii=False))
        return

    if args.mode == "cli":
        executor.run_cli_loop(
            banner="Simple Test Agent CLI (type 'exit' to quit)",
            print_tool_response=True,
            clear_tool_metadata_each_turn=True,
        )
        return

    if args.mode == "agentos":
        executor.run_agent_os(
            id=args.agent_id,
            name="Simple Test Agent",
            description="Standalone test agent for unified executor.",
            host=args.host,
            port=args.port,
        )
        return

    client = AgentExecutor.create_api_client(
        agent_id=args.agent_id,
        host=args.host,
        port=args.port,
    )

    if args.mode == "api-direct":
        result = client.run_direct(
            message=args.ask,
            session_id=args.session_id,
            user_id=args.user_id,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    for event in client.run_stream(
        message=args.ask,
        session_id=args.session_id,
        user_id=args.user_id,
    ):
        event_type = event.get("event")
        if event_type == "RunContent":
            print(event.get("content", ""), end="", flush=True)
        elif event_type in {"ToolCallStarted", "ToolCallCompleted"}:
            tool_name = event.get("tool", {}).get("tool_name", "unknown")
            print(f"\n[{event_type}] {tool_name}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        raise RuntimeError(f"Failed to execute test flow: {str(e)}") from e

# python -m src.agents.agent_executor.test