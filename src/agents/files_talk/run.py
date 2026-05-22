from src.agents.files_talk.agent import FileTalkAgent
from src.agents.utils.agno_agent_executor import AgnoAgentExecutor
from src.utils.unique_id_factory import IDGenerator

if __name__ == "__main__":
    AgnoAgentExecutor(
        agent_class=FileTalkAgent,
        params={
            "filter_search": {
                "knowledge_base_id": ["test_agent"]
            }
        },
        # session_id e user_id são opcionais — omita para usar os defaults
        # session_id=IDGenerator().uuid(),
        # user_id="user_01",
    ).run()

# python -m src.agents.files_talk.run