from src.utils.unique_id_factory import IDGenerator

from src.agents.datafram_agent.agent import BaseAgent
from src.agents.utils.test_agents.agno_agent_executor import AgnoAgentExecutor


if __name__ == "__main__":
    AgnoAgentExecutor(
        agent_class=BaseAgent,
        params={
            "citys": ["Salvador", "São Paulo", "Rio de Janeiro"]
        },
        # session_id e user_id são opcionais — omita para usar os defaults
        # session_id=IDGenerator().uuid(),
        # user_id="user_01",
        print_tool_response=True
    ).run()

# python -m src.agents.datafram_agent.run