import json
from rich.console import Console
from rich.panel import Panel

from src.agents.files_talk.agent import FileTalkAgent

from src.agents.utils.agno_ai_agents import AgnoAiAgents
from src.agents.utils.test_agents.run_agent import RunAgent

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
            "session_id": "12345",
            "user_id": "user_01",
            "filter_search": {
                "file_id": ["candidatura", "tenerezza", "cucinare"]
            }
        }
    )

    console = Console()
    runner = RunAgent(agent=agent)

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