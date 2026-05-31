from src.utils.unique_id_factory import IDGenerator

from src.agents.trend_radar.agent import BaseAgent
from src.agents.utils.test_agents.agno_agent_executor import AgnoAgentExecutor
from src.agents.utils.test_agents.run_agent import RunAgent

if __name__ == "__main__":
    
    # CLI
    cli_runner = AgnoAgentExecutor(
        agent_class=BaseAgent,
        params={
            "citys": ["Salvador", "São Paulo", "Rio de Janeiro"]
        },
        # session_id e user_id são opcionais — omita para usar os defaults
        # session_id=IDGenerator().uuid(),
        # user_id="user_01",
        print_tool_response=True
    )

    #cli_runner.run()

    # AgentOS
    agent_os_runner = RunAgent(agent=BaseAgent().create_agent(metadata={"session_id": "122", "user_id": "user_01" }))
    agent_os_runner.agent_os()

# python -m src.agents.trend_radar.run