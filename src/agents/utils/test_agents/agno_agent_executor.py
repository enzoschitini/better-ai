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
    Executor genérico para agentes Agno.

    Encapsula o ciclo completo: registro, criação e loop interativo.
    session_id e user_id são opcionais — gerados/defaultados automaticamente.

    Uso:
        executor = AgnoAgentExecutor(
            agent_class=FileTalkAgent,
            params={
                "filter_search": {
                    "knowledge_base_id": ["test_agent"]
                }
            }
        )
        executor.run()
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
        """Monta o dict de parâmetros mesclando session/user com os extras."""
        return {
            "session_id": self._session_id,
            "user_id": self._user_id,
            **self._extra_params,
        }

    def _setup(self) -> None:
        """Registra e instancia o agente."""
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
        """Inicia o loop interativo do agente."""
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