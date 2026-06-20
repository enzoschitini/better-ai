from typing import List, Any

from agno.tools import Toolkit
from src.agents.utils.tool_context import ToolContext

# Retriver Packages
from src.vector_store.pinecone.client import PineconeClient
from src.vector_store.pinecone.retriever import PineconeRetriever
from src.vector_store.pinecone.utils.retrieval_manager import RetrievalManager
from src.agents.knowlegbase_agent.config import (
    PINECONE_INDEX_NAME, PINECONE_MAIN_NAMESPACE
)
class Toolkit(Toolkit):
    """
    Toolkit is a generic toolkit template for building agent tools.

    Use this as a starting point for creating new toolkits by:
    - Renaming the class to reflect the toolkit's domain
    - Adding domain-specific tools as methods
    - Registering them in the `tools` list inside `__init__`

    Args:
        enable_get_context (bool): Enable the get context tool. Default is True.
        all (bool): Enable all tools. Overrides individual flags when True. Default is False.
        tool_context (ToolContext): Optional metadata collector. Default is None.
    """
    def __init__(
        self,
        filter_search: dict,
        enable_get_context: bool = True,
        all: bool = False,
        tool_context: ToolContext = None,
        **kwargs,
    ):
        self.filter_search = filter_search
        self.tool_context = tool_context
        tools: List[Any] = []

        if all or enable_get_context:
            tools.append(self.get_context)

        super().__init__(name="toolkit", tools=tools, **kwargs)

    def _update_response(self, tool_name: str, payload: dict):
        """
        Internal helper to collect metadata about tool execution.
        """
        if self.tool_context:
            self.tool_context.add_metadata(
                tool_name=tool_name,
                payload=payload
            )
    
    def get_context(self, query: str) -> str:
        """
        Retrieve relevant documents based on a user query.

        This tool performs semantic search over a document collection and returns
        the most relevant results according to the provided query.

        Args:
            query (str):
                The user's search query. Must be a non-empty string with meaningful content.
                If the query is empty, None, or invalid, the tool will return an error message
                indicating that a valid query is required.

        Returns:
            str:
                A JSON-formatted string containing the retrieved documents and their relevance scores,
                or an error message if the input is invalid (e.g., empty query or invalid max_results).

        Notes:
            - This tool should only be used when there is a clear search intent.
            - Avoid calling this tool with empty or undefined query values.
            - If no relevant documents are found, an empty result or informative message may be returned.
        """
        try:
            pine_client = PineconeClient(
                index_name=PINECONE_INDEX_NAME,
                main_namespace=PINECONE_MAIN_NAMESPACE
            )
            retriver = PineconeRetriever(pine_client)

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

            print(f"Retrieved {len(documents)}")

        except Exception as e:
            return f"Failed to generate context of relevant documents: {str(e)}"

        return context

if __name__ == "__main__":
    toolkit = Toolkit(filter_search={})
    result = toolkit.get_context("Resuma a base")
    print(result)


# python -m src.agents.knowlegbase_agent.tools.toolkit