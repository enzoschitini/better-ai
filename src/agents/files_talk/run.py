import json
from rich.console import Console
from rich.panel import Panel

from src.agents.files_talk.agent import FileTalkAgent
from src.agents.files_talk.config import AGENT_AI_BANNER

from src.agents.utils.agno_ai_agents import AgnoAiAgents
from src.agents.utils.test_agents.run_agent import RunAgent
from src.utils.unique_id_factory import IDGenerator

if __name__ == "__main__":
    # =========================
    # FACTORY
    # =========================
    agno = AgnoAiAgents()
    agno.register("FileTalkAgent", FileTalkAgent)

    # =========================
    # CREATE
    # =========================
    agent, tool_context = agno.create_agent(
        "FileTalkAgent",
        {
            "session_id": IDGenerator().uuid(),
            "user_id": "user_01",
            "filter_search": {
                "knowledge_base_id": ["test_agent"]
            }
        }
    )

    console = Console()
    runner = RunAgent(agent=agent)
    print(AGENT_AI_BANNER)

    while True:
        ask = input("\n>>> ")

        if ask.lower() in ["exit", "quit", "cls", "sair"]:
            print("In closing...")
            break

        try:
            response = runner.debug(ask=ask)

            print_tool_response = False
            if print_tool_response:
                console.print(
                    Panel(
                        f"{json.dumps(tool_context.tool_responser.get_metadata(), indent=4, ensure_ascii=False)}",
                        title="Tool Response Metadata",
                        border_style="cyan"
                    )
                )

        except Exception as e:
            print(f"Error: {e}")

# python -m src.agents.files_talk.run