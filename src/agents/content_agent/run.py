from src.utils.unique_id_factory import IDGenerator

from src.agents.content_agent.agent import ContentAgent
from src.agents.agent_executor import AgentExecutor


if __name__ == "__main__":
    executor = AgentExecutor.from_agent_class(
        # session_id e user_id são opcionais — omita para usar os defaults
        # session_id=IDGenerator().uuid(),
        # user_id="user_01",
        agent_class=ContentAgent,
        params={
            "filter_search": {
                "collection_id": ["oboticario"]
            },
            "generate_content_metadata": {
                "model_id": "gpt-4.1-mini",
                "max_results": 5,
                "content_count": 2,
                "body_min_chars": 700,
                "body_max_chars": 1200,
                "objective": "Generate structured content variants based on the retrieved context, following the specified requirements.",
                "extra_requirements": (
                    "- Create engaging Instagram posts focused on marketing trends for men's perfumes, highlighting products from the Malbec line.\n"
                    "- Include information about olfactory notes and usage suggestions.\n"
                )
            }
        },
    )

    executor.run_cli_loop()

# Criar um post para Instagram focado em tendências de mercado para perfumes masculinos, destacando os produtos da linha Malbec. Inclua informações sobre notas olfativas e sugestões de uso.
# Quero um post sobre o Malbec

# python -m src.agents.content_agent.run