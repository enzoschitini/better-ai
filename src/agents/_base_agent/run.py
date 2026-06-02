from src.utils.unique_id_factory import IDGenerator

from src.agents._base_agent.agent import BaseAgent
from src.agents.agent_executor import UnifiedAgentExecutor


if __name__ == "__main__":
    executor = UnifiedAgentExecutor.from_agent_class(
        agent_class=BaseAgent,
        params={
            "citys": ["Salvador", "São Paulo", "Rio de Janeiro"]
        },
        # session_id e user_id são opcionais — omita para usar os defaults
        # session_id=IDGenerator().uuid(),
        # user_id="user_01",
    )
    executor.run_cli_loop(print_tool_response=True)

# python -m src.agents._base_agent.run