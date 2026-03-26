from dotenv import load_dotenv
from typing import List, Any

from agno.tools import Toolkit

# Retriver Package
from src.vector_store.pinecone.pinecone_retriever import PineconeRetriever
from src.vector_store.pinecone.utils.retrieval_manager import RetrievalManager

load_dotenv()

class RetrievalAugmentedGeneration(Toolkit):
    """
    Toolkit for structured data analysis using DataFrames.

    This toolkit provides tools to:
    - explore tabular datasets
    - generate statistical summaries
    - identify patterns and insights
    - produce analytical reports

    Args:
        enable_dataframe_analyzer (bool): Enables the dataframe analysis tool. Defaults to True.
        all (bool): Enables all available tools. Overrides individual flags when True. Defaults to False.
        TOOL_RESPONSER (Any): Optional object responsible for collecting tool execution metadata.
    """
    def __init__(
        self,
        filter_search: dict,
        enable_get_relevant_documents: bool = True,
        all: bool = False,
        TOOL_RESPONSER: Any = None,
        **kwargs,
    ):
        self.filter_search = filter_search
        self.TOOL_RESPONSER = TOOL_RESPONSER
        tools: List[Any] = []

        if all or enable_get_relevant_documents:
            tools.append(self.get_relevant_documents)

        super().__init__(name="get_relevant_documents_tools", tools=tools, **kwargs)
    
    def _update_response(self, tool_name: str, payload: dict):
        """
        Internal helper method used to collect metadata about tool execution.
        """
        if self.TOOL_RESPONSER:
            self.TOOL_RESPONSER.add_metadata(
                tool_name=tool_name,
                payload=payload
            )

    def get_relevant_documents(self, query: str) -> str:
        """
        dataframe_analyzer is a tool for runs an automated analysis on a DataFrame and returns a structured report based on a user-provided query.

        ⚠️ IMPORTANT:
        - The dataset is ALREADY loaded internally.
        - The user DOES NOT need to provide any file or data.
        - NEVER ask the user for the dataset.
        - ALWAYS execute the analysis using the available internal data.

        The tool is responsible for:
        - interpreting the query
        - analyzing the internal dataframe
        - generating insights and visualizations (if applicable)

        Args:
            query (str): User query or instruction related to the dataset
                         (e.g., "analyze sales by region", "find revenue patterns").

        Returns:
            str: A report containing analysis results, insights, and possible visualizations. IN MARKDOWN
        """
        try:
            retriver = PineconeRetriever()

            documents = retriver.similarity_search(
                query=query,
                k=5,
                filter_search=self.filter_search
            )

            manager = RetrievalManager(docs=documents)
            context = manager.generate_context()

            # Collect metadata
            self._update_response(
                "get_relevant_documents", 
                {"files": manager.get_files()}
            )

        except Exception as e:
            return f"Failed to generate context of research: {str(e)}"

        return context

if __name__ == "__main__":
    import json

    tool = RetrievalAugmentedGeneration(
        filter_search={
            "file_id": ["candidatura", "tenerezza", "cucinare"]
        }
    )
    result = tool.get_relevant_documents("Enzo Schitini")

    print(f"\n\n{result}\n")


# python -m src.agents.rag.toolkit