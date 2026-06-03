from typing import Any, Dict, Iterator, Optional, Sequence, Set, Type

from agno.agent import Agent
from agno.os import AgentOS
from rich.console import Console
from rich.panel import Panel

from src.agents.agent_executor.agent_factory import LocalAgentFactory
from src.agents.agent_executor.api_client import AgentApiClient
from src.agents.agent_executor.response_formatter import ResponseFormatter
from src.agents.agent_executor.tool_collector import ToolCollector
from src.utils.unique_id_factory import IDGenerator


class AgentExecutor:
    """
    Single execution interface for Agno agents.

    Supported modes:
    1. JSON output from direct run.
    2. AgentOS server mode.
    3. CLI print_response mode with tool collection.
    4. API mode (direct and stream) via AgentOS endpoint.
    """

    DEFAULT_USER_ID = "user_01"

    def __init__(
        self,
        agent: Agent,
        *,
        tool_collector: Optional[ToolCollector] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        console: Optional[Console] = None,
    ):
        self.agent = agent
        self.session_id = session_id
        self.user_id = user_id
        self.tool_collector = tool_collector or ToolCollector()
        self.console = console or Console()

    @classmethod
    def from_agent_class(
        cls,
        agent_class: Type,
        params: Optional[Dict[str, Any]] = None,
        *,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> "AgentExecutor":
        current_session_id = session_id or IDGenerator().uuid()
        current_user_id = user_id or cls.DEFAULT_USER_ID

        metadata = {
            "session_id": current_session_id,
            "user_id": current_user_id,
            **(params or {}),
        }

        factory = LocalAgentFactory()
        agent_name = agent_class.__name__
        factory.register(agent_name, agent_class)
        agent, tool_context = factory.create_agent(agent_name, metadata)

        collector = ToolCollector(tool_context.tool_responser)
        return cls(
            agent=agent,
            tool_collector=collector,
            session_id=current_session_id,
            user_id=current_user_id,
        )

    # ------------------------------------------------------------------
    # 1) Simple JSON mode
    # ------------------------------------------------------------------

    def run_json(
        self,
        ask: str = "Hello!",
        *,
        output_path: Optional[str] = None,
        include_tool_metadata: bool = True,
        clear_tool_metadata: bool = False,
    ) -> Dict[str, Any]:
        try:
            response = self.agent.run(input=ask, stream=False)
        except Exception as e:
            raise RuntimeError(f"Failed to execute agent in JSON mode: {str(e)}")

        formatted = ResponseFormatter(response).format()

        if include_tool_metadata:
            formatted["tool_metadata"] = self.tool_collector.collect()

        if output_path:
            ResponseFormatter.save_json(formatted, output_path)

        if clear_tool_metadata:
            self.tool_collector.clear()

        return formatted

    def run_stream(
        self,
        ask: str = "Hello!",
        *,
        clear_tool_metadata: bool = False,
    ) -> Iterator[Any]:
        """
        Run the agent in stream mode and yield partial outputs incrementally.

        This method does not format or persist JSON output.
        """
        try:
            stream_response = self.agent.run(input=ask, stream=True)
        except Exception as e:
            raise RuntimeError(f"Failed to execute agent in stream mode: {str(e)}") from e

        try:
            for chunk in stream_response:
                yield chunk
        finally:
            if clear_tool_metadata:
                self.tool_collector.clear()

    @staticmethod
    def parse_stream_chunk(chunk: Any) -> Dict[str, Any]:
        """
        Normalize stream chunks/events into a consistent structure.

        This avoids dealing with raw objects such as RunContentEvent(...)
        directly in CLI tests.
        """
        parsed: Dict[str, Any] = {
            "event": None,
            "content": "",
            "reasoning_content": "",
            "run_id": None,
            "session_id": None,
            "raw": chunk,
        }

        if chunk is None:
            return parsed

        if isinstance(chunk, str):
            parsed["content"] = chunk
            return parsed

        if isinstance(chunk, dict):
            parsed["event"] = chunk.get("event")
            parsed["run_id"] = chunk.get("run_id")
            parsed["session_id"] = chunk.get("session_id")

            for key in ("content", "text", "delta"):
                value = chunk.get(key)
                if isinstance(value, str) and value:
                    parsed["content"] = value
                    break

            reasoning = chunk.get("reasoning_content")
            if isinstance(reasoning, str) and reasoning:
                parsed["reasoning_content"] = reasoning

            return parsed

        parsed["event"] = getattr(chunk, "event", None)
        parsed["run_id"] = getattr(chunk, "run_id", None)
        parsed["session_id"] = getattr(chunk, "session_id", None)

        for attr in ("content", "text", "delta"):
            value = getattr(chunk, attr, None)
            if isinstance(value, str) and value:
                parsed["content"] = value
                break

        reasoning_attr = getattr(chunk, "reasoning_content", None)
        if isinstance(reasoning_attr, str) and reasoning_attr:
            parsed["reasoning_content"] = reasoning_attr

        return parsed

    def run_stream_print(
        self,
        ask: str = "Hello!",
        *,
        clear_tool_metadata: bool = False,
        print_newline: bool = True,
    ) -> None:
        """
        Run stream mode and print parsed chunks incrementally.
        """
        try:
            for chunk in self.run_stream(
                ask=ask,
                clear_tool_metadata=clear_tool_metadata,
            ):
                parsed_chunk = self.parse_stream_chunk(chunk)
                content = parsed_chunk.get("content", "")
                if content:
                    print(content, end="", flush=True)
        except Exception as e:
            raise RuntimeError(f"Failed to print stream mode response: {str(e)}") from e

        if print_newline:
            print()

    # ------------------------------------------------------------------
    # 2) AgentOS mode
    # ------------------------------------------------------------------

    def run_agent_os(
        self,
        *,
        id: str = "my_agent",
        name: str = "My Agent",
        description: str = "An agent created for demonstration purposes.",
        host: str = "localhost",
        port: int = 7777,
    ) -> None:
        try:
            agent_os = AgentOS(
                id=id,
                name=name,
                description=description,
                agents=[self.agent],
            )

            app = agent_os.get_app()
            agent_os.serve(app=app, host=host, port=port)
        except Exception as e:
            raise RuntimeError(f"Failed to start AgentOS mode: {str(e)}")

    # ------------------------------------------------------------------
    # 3) CLI / print_response mode + tool collector
    # ------------------------------------------------------------------

    def run_print_response(
        self,
        ask: str,
        *,
        show_message: bool = True,
        show_reasoning: bool = True,
        show_full_reasoning: bool = False,
        tags_to_include_in_markdown: Optional[Set[str]] = None,
        print_tool_response: bool = False,
        clear_tool_metadata: bool = False,
    ) -> Dict[str, Any]:
        try:
            self.agent.print_response(
                ask,
                show_message=show_message,
                show_reasoning=show_reasoning,
                show_full_reasoning=show_full_reasoning,
                tags_to_include_in_markdown=tags_to_include_in_markdown,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to execute print_response mode: {str(e)}")

        tool_metadata = self.tool_collector.collect()
        if print_tool_response and tool_metadata:
            self.console.print(
                Panel(
                    self.tool_collector.collect_as_json(),
                    title="Tool Response Metadata",
                    border_style="cyan",
                )
            )

        if clear_tool_metadata:
            self.tool_collector.clear()

        return tool_metadata

    def run_cli_loop(
        self,
        *,
        banner: Optional[str] = None,
        print_tool_response: bool = True,
        clear_tool_metadata_each_turn: bool = True,
        exit_commands: Optional[Sequence[str]] = None,
    ) -> None:
        if banner:
            print(banner)

        exit_set = set(exit_commands or ["exit", "quit", "cls", "sair"])

        while True:
            ask = input("\n>>> ").strip()
            if not ask:
                continue

            if ask.lower() in exit_set:
                print("Shutdown...")
                break

            try:
                self.run_print_response(
                    ask,
                    print_tool_response=print_tool_response,
                    clear_tool_metadata=clear_tool_metadata_each_turn,
                )
            except Exception as e:
                print(f"Error: {e}")

    # ------------------------------------------------------------------
    # 4) API mode (direct and stream)
    # ------------------------------------------------------------------

    @staticmethod
    def create_api_client(agent_id: str, host: str = "localhost", port: int = 7777) -> AgentApiClient:
        return AgentApiClient(agent_id=agent_id, host=host, port=port)
