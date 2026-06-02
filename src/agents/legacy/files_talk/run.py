from agents.legacy.files_talk.agent import FileTalkAgent
from src.agents.agent_executor import AgentExecutor
from src.utils.unique_id_factory import IDGenerator

if __name__ == "__main__":
    executor = AgentExecutor.from_agent_class(
        agent_class=FileTalkAgent,
        params={
            "filter_search": {
                "knowledge_base_id": ["test_agent"]
            }
        },
        # session_id e user_id são opcionais — omita para usar os defaults
        # session_id=IDGenerator().uuid(),
        # user_id="user_01",
    )
    executor.run_cli_loop(print_tool_response=False)

# python -m src.agents.files_talk.run