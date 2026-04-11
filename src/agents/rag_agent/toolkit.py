from dotenv import load_dotenv
from typing import List, Any

from agno.tools import Toolkit
from src.agents.ultils.tool_response import ToolResponse

# Retriver Packages
from src.vector_store.pinecone.pinecone_retriever import PineconeRetriever
from src.vector_store.pinecone.utils.retrieval_manager import RetrievalManager

load_dotenv()

class RetrievalAugmentedGeneration(Toolkit):
    """
    RetrievalAugmentedGeneration is a toolkit for retrieval-augmented generation (RAG) tasks.
    
    This toolkit can:
    - Retrieve relevant documents based on a user-provided query and filter criteria.
    - Generate a context of relevant documents for use in RAG applications.

    Use this toolkit for:
    - Responding to user queries with relevant information from a document collection.
    - Analyzing and summarizing retrieved documents to provide concise answers.
    - Generate insights and recommendations based on the retrieved context.
    
    Args:
        enable_get_relevant_documents (bool): Enable the tool for retrieving relevant documents. Default is True.
        all (bool): Enable all tools. Overrides individual flags when True. Default is False.
    """
    def __init__(
        self,
        filter_search: dict,
        enable_get_relevant_documents: bool = True,
        all: bool = False,
        TOOL_RESPONSER: ToolResponse = None,
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

    def get_relevant_documents(self, query: str, max_results: int) -> str:
        """
        Retrieve relevant documents based on a user query.

        This tool performs semantic search over a document collection and returns
        the most relevant results according to the provided query.

        Args:
            query (str):
                The user's search query. Must be a non-empty string with meaningful content.
                If the query is empty, None, or invalid, the tool will return an error message
                indicating that a valid query is required.

            max_results (int):
                The maximum number of documents to retrieve. Must be between 1 and 15.
                Values outside this range may be automatically adjusted or return an error.

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
            retriver = PineconeRetriever()

            documents = retriver.similarity_search(
                query=query,
                k=max_results,
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
            return f"Failed to generate context of relevant documents: {str(e)}"

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


# python -m src.agents.rag_agent.toolkit