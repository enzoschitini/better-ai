import json

from src.agents.rag_agent.tools.toolkit import RetrievalAugmentedGeneration


tool = RetrievalAugmentedGeneration(
    filter_search={
        "collection_id": ["oboticario"]
    }
)
result = tool.get_relevant_documents("Malbec", 5)

print(f"\n\n{result}\n")

# python -m src.agents.rag_agent.tools.content_generation