from dotenv import load_dotenv
from typing import List, Any

from agno.tools import Toolkit
from src.agents.utils.tool_context import ToolContext

# Retriver Packages
from src.vector_store.pinecone.client import PineconeClient
from src.vector_store.pinecone.retriever import PineconeRetriever
from src.vector_store.pinecone.utils.retrieval_manager import RetrievalManager

from src.agents.content_agent.tools.content_generation.config import (
    PINECONE_INDEX_NAME, PINECONE_MAIN_NAMESPACE
)

load_dotenv()

class RetrievalAugmentedGeneration(Toolkit):
    """
    RetrievalAugmentedGeneration is a toolkit for retrieval-augmented generation (RAG) tasks.
    
    This toolkit can:
    - Retrieve relevant documents based on a user-provided query and filter criteria.
    - Generate a context of relevant documents for use in RAG applications.
    - Generate markdown-formatted content using the retrieved context as input for a content generation pipeline.

    Use this toolkit for:
    - Responding to user queries with relevant information from a document collection.
    - Analyzing and summarizing retrieved documents to provide concise answers.
    - Generate insights and recommendations based on the retrieved context.
    - Create markdown-formatted content for documentation or reporting purposes.
    
    Args:
        enable_get_relevant_documents (bool): Enable the tool for retrieving relevant documents. Default is True.
        enable_generate_content (bool): Enable the tool for generating content using retrieval context. Default is False.
        all (bool): Enable all tools. Overrides individual flags when True. Default is False.
    """
    def __init__(
        self,
        filter_search: dict,
        generate_content_metadata: dict = None,
        enable_get_relevant_documents: bool = True,
        enable_generate_content: bool = True,
        all: bool = False,
        tool_context: ToolContext = None,
        **kwargs,
    ):
        self.filter_search = filter_search
        self.generate_content_metadata = generate_content_metadata
        self.tool_context = tool_context
        tools: List[Any] = []

        if all or enable_get_relevant_documents:
            tools.append(self.get_relevant_documents)
        if all or enable_generate_content:
            tools.append(self.generate_content)

        super().__init__(name="get_relevant_documents_tools", tools=tools, **kwargs)
    
    def _update_response(self, tool_name: str, payload: dict):
        """
        Internal helper method used to collect metadata about tool execution.
        """
        if self.tool_context:
            self.tool_context.add_metadata(
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
            pine_client = PineconeClient(
                index_name=PINECONE_INDEX_NAME,
                main_namespace=PINECONE_MAIN_NAMESPACE
            )
            retriver = PineconeRetriever(pine_client)

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
        
    def generate_content(self, query: str) -> str:
        """
        Generate markdown-ready content using retrieval-augmented generation.

        This method calls the content generation pipeline to retrieve relevant context,
        generate one structured post, and convert the result into a markdown string.

        Args:
            query (str):
                The user prompt that guides retrieval and content generation.

        Returns:
            str:
                A markdown-formatted content output when generation succeeds,
                or an error message string when generation fails.
        """
        try:
            from src.agents.content_agent.tools.content_generation.module import GenerateContent
            from src.agents.content_agent.tools.content_generation.markdown_utils import MarkdownContent

            print(f"Generating content for query: {query}")

            filter_search = self.filter_search
            metadata = self.generate_content_metadata or {}

            generator = GenerateContent(
                **{"model_id": metadata["model_id"]} if "model_id" in metadata else {},
                filter_search=filter_search,
            )

            optional_params = {}
            for key in ["max_results", "content_count", "body_min_chars", "body_max_chars", "extra_requirements"]:
                if key in metadata:
                    optional_params[key] = metadata[key]

            generated_content = generator.generate(
                query=query,
                objective=metadata.get("objective", "Generate a structured post based on the retrieved context."),
                **optional_params
            )

            markdown_content = MarkdownContent.format_posts_json_to_markdown(
                posts_payload=generated_content,
            )

            final_payload = (
                "<<<FINAL_ANSWER_START>>>\n"
                f"{markdown_content}\n"
                "<<<FINAL_ANSWER_END>>>"
            )

            self._update_response(
                "generate_content",
                {
                    "query": query,
                    "max_results": metadata.get("max_results"),
                    "markdown_content": markdown_content,
                    "generated_content": generated_content.model_dump() if hasattr(generated_content, "model_dump") else generated_content,
                },
            )

            return final_payload
        except Exception as e:
            return f"Failed to generate content using retrieval context: {str(e)}"


if __name__ == "__main__":
    import json

    tool = RetrievalAugmentedGeneration(
        filter_search={
            "collection_id": ["oboticario"]
        },
        generate_content_metadata={
            "model_id": "gpt-4.1-mini",
            "objective": "Generate a structured post based on the retrieved context.",
            "max_results": 5,
            "content_count": 1,
            "body_min_chars": 300,
            "body_max_chars": 500,
            #"extra_requirements": "- Focus on market trends for men's perfumes, highlighting products from the Malbec line.\n- Include information about olfactory notes and usage suggestions."
        }
    )

    #result = tool.get_relevant_documents("Raccontare", 5)
    result = tool.generate_content(
        "Crie um posts com os arquivos da base", 
    )

    print(f"\n\n{result}\n")

# python -m src.agents.content_agent.tools.toolkit