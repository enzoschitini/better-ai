# src/agents/utils/agno_agent_executor.py

import json
from rich.console import Console
from rich.panel import Panel

from src.agents.utils.agno_ai_agents import AgnoAiAgents
from src.agents.utils.test_agents.run_agent import RunAgent
from src.utils.unique_id_factory import IDGenerator

from src.agents.utils.test_agents.config import AGENT_AI_BANNER

class AgnoAgentExecutor:
    """
    Orchestrates the full lifecycle of an Agno AI agent, handling setup, session management,
    tool response display, and the interactive run loop.

    Args:
        :param agent_class (type): The agent class to be registered and instantiated.
        :param params (dict | None): Optional extra parameters forwarded to the agent constructor. Default is None.
        :param session_id (str | None): Unique identifier for the session. Default is None (auto-generated via IDGenerator).
        :param user_id (str | None): Identifier for the user interacting with the agent. Default is "user_01".
        :param print_tool_response (bool): Whether to print tool response metadata after each agent run. Default is False.
        :param banner (str | None): Banner text displayed at the start of the run loop. Default is None (resolved from the agent class or AGENT_AI_BANNER).

    Methods:
        run(): Starts the interactive CLI loop, reading user input and dispatching it to the agent.
    """

    DEFAULT_USER_ID = "user_01"

    def __init__(
        self,
        agent_class: type,
        params: dict | None = None,
        *,
        session_id: str | None = None,
        user_id: str | None = None,
        print_tool_response: bool = False,
        banner: str | None = None,
    ) -> None:
        self._agent_class = agent_class
        self._agent_name = agent_class.__name__
        self._extra_params = params or {}
        self._print_tool_response = print_tool_response
        self._banner = banner or getattr(agent_class, "BANNER", None) or AGENT_AI_BANNER

        self._session_id = session_id or IDGenerator().uuid()
        self._user_id = user_id or self.DEFAULT_USER_ID

        self._console = Console()
        self._agent = None
        self._tool_context = None
        self._runner = None

        self._setup()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _build_params(self) -> dict:
        """
        Assembles the parameter dictionary used to instantiate the agent, merging session
        context with any extra parameters provided at construction time.

        Returns:
            dict: A dictionary containing session_id, user_id, and any additional extra parameters.
        """
        return {
            "session_id": self._session_id,
            "user_id": self._user_id,
            **self._extra_params,
        }

    def _setup(self) -> None:
        """
        Initializes and wires up all internal components by registering the agent class,
        creating the agent instance with its tool context, and preparing the runner.
        """
        agno = AgnoAiAgents()
        agno.register(self._agent_name, self._agent_class)

        self._agent, self._tool_context = agno.create_agent(
            self._agent_name,
            self._build_params(),
        )
        self._runner = RunAgent(agent=self._agent)

    # ------------------------------------------------------------------
    # Tool response
    # ------------------------------------------------------------------

    def _print_tools(self) -> None:
        """
        Conditionally fetches and renders the tool response metadata as a formatted Rich panel
        in the console, only when print_tool_response is enabled.
        """
        if not self._print_tool_response:
            return

        metadata = json.dumps(
            self._tool_context.tool_responser.get_metadata(),
            indent=4,
            ensure_ascii=False,
        )
        self._console.print(
            Panel(metadata, title="Tool Response Metadata", border_style="cyan")
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> None:
        """
        Starts the interactive CLI loop that continuously reads user input, dispatches it to
        the agent via the runner, and optionally prints tool response metadata after each turn.
        """
        print(self._banner)

        while True:
            ask = input("\n>>> ").strip()

            if not ask:
                continue

            if ask.lower() in {"exit", "quit", "cls", "sair"}:
                print("Shutdown...")
                break

            try:
                self._runner.debug(ask=ask)
                self._print_tools()

            except Exception as e:  # noqa: BLE001
                print(f"Error: {e}")


# python -m rc.agents.utils.test_agents.agno_agent_executor