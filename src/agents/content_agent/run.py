from src.utils.unique_id_factory import IDGenerator

from src.agents.content_agent.agent import ContentAgent
from src.agents.agent_executor import AgentExecutor


if __name__ == "__main__":
    executor = AgentExecutor.from_agent_class(
        agent_class=ContentAgent,
        params={
            "filter_search": {
                "collection_id": ["oboticario"]
            }
        },
        # session_id e user_id são opcionais — omita para usar os defaults
        # session_id=IDGenerator().uuid(),
        # user_id="user_01",
    )
    executor.run_cli_loop(print_tool_response=True)

# Criar um post para Instagram focado em tendências de mercado para perfumes masculinos, destacando os produtos da linha Malbec. Inclua informações sobre notas olfativas e sugestões de uso.

# python -m src.agents.content_agent.run