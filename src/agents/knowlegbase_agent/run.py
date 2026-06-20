from src.utils.unique_id_factory import IDGenerator

from src.agents.knowlegbase_agent.agent import KnowledgeBaseAgent
from src.agents.agent_executor import AgentExecutor


if __name__ == "__main__":
    executor = AgentExecutor.from_agent_class(
        agent_class=KnowledgeBaseAgent,
        params={
            "filter_search": {}
        },
        # session_id e user_id são opcionais — omita para usar os defaults
        # session_id=IDGenerator().uuid(),
        # user_id="user_01",
    )
    executor.run_cli_loop(print_tool_response=True)

# python -m src.agents.knowlegbase_agent.run