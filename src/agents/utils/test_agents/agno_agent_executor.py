# src/agents/utils/agno_agent_executor.py

from src.agents.agent_executor import AgentExecutor

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
        self._extra_params = params or {}
        self._print_tool_response = print_tool_response
        self._banner = banner or getattr(agent_class, "BANNER", None) or AGENT_AI_BANNER

        self._session_id = session_id
        self._user_id = user_id or self.DEFAULT_USER_ID
        self._executor = None

        self._setup()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup(self) -> None:
        """
        Initializes the unified executor using the agent class factory.
        """
        self._executor = AgentExecutor.from_agent_class(
            agent_class=self._agent_class,
            params=self._extra_params,
            session_id=self._session_id,
            user_id=self._user_id,
        )

    # ------------------------------------------------------------------
    # Tool response
    # ------------------------------------------------------------------

    def _print_tools(self) -> None:
        """
        Backward-compatible method kept for legacy calls.
        """
        return
    
    def clean_tool_response(self) -> None:
        """
        Clears the stored tool response metadata from the tool context's responser.
        """
        if self._executor is not None:
            self._executor.tool_collector.clear()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> None:
        """
        Starts the interactive CLI loop with tool collector integration.
        """
        if self._executor is None:
            raise RuntimeError("Executor is not initialized")

        self._executor.run_cli_loop(
            banner=self._banner,
            print_tool_response=self._print_tool_response,
            clear_tool_metadata_each_turn=True,
        )


# python -m rc.src.agents.utils.test_agents.agno_agent_executor