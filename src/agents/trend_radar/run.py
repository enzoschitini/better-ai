from src.utils.unique_id_factory import IDGenerator

from src.agents.trend_radar.agent import BaseAgent
from src.agents.agent_executor import AgentExecutor

if __name__ == "__main__":
    # CLI
    runner = AgentExecutor.from_agent_class(
        agent_class=BaseAgent,
        params={
            "citys": ["Salvador", "São Paulo", "Rio de Janeiro"]
        },
        # session_id e user_id são opcionais — omita para usar os defaults
        # session_id=IDGenerator().uuid(),
        # user_id="user_01",
    )

    for chunk in runner.run_stream(ask="Hello!"):
        print(chunk, end="", flush=True)

    print()

    # JSON (alternativo)
    # runner.run_json()

    # AgentOS
    #runner.run_agent_os(id="trend_radar", name="Trend Radar")

# python -m src.agents.trend_radar.run