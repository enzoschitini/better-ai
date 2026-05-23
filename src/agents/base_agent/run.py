from src.utils.unique_id_factory import IDGenerator

from src.agents.base_agent.agent import BaseAgent
from src.agents.utils.test_agents.agno_agent_executor import AgnoAgentExecutor


if __name__ == "__main__":
    AgnoAgentExecutor(
        agent_class=BaseAgent,
        params={
            "filter_search": {
                "knowledge_base_id": ["test_agent"]
            }
        },
        # session_id e user_id são opcionais — omita para usar os defaults
        # session_id=IDGenerator().uuid(),
        # user_id="user_01",
    ).run()

# python -m src.agents.base_agent.run