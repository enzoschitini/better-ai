```python
import logging
from typing import List, Optional, Dict, Any, Union

from src.vector_store.pinecone.client import PineconeClient
from src.vector_store.config import PineconeVectorStoreConfig
from src.tracing.tracing_core import ApplicationTracing

logging.getLogger("httpx").setLevel(logging.WARNING)

tracer = ApplicationTracing(
    flag="PineconeRetriever",
    file_name="pinecone_retriever.py",
    log_file_name="pinecone_module"
)

class PineconeRetriever:
    """
    PineconeRetriever is a specialized class designed to interact with the Pinecone vector 
    search service, allowing efficient retrieval of documents based on vector similarity and metadata filtering.
    It manages the embedding model, index connection, and supports advanced querying features such as filters and pagination.
    
    Args:
    :param client (Optional[PineconeClient]): A PineconeClient instance to handle indexing and embedding operations. Default is None, which creates a new PineconeClient internally.

    Methods:
            similarity_search(): Performs a similarity search over the Pinecone index using a text query, returning the most relevant documents.
            get_all_docs_by_metadata(): Retrieves all documents matching specified metadata filters using paginated queries.
    """
    def __init__(self, client: Optional[PineconeClient] = None):
        tracer.INFO("__init__", "Initializing retriever")

        try:
            if not client:
                tracer.DEBUG("__init__", "No client provided, creating default client")
                client = PineconeClient()

            self.config = PineconeVectorStoreConfig()
            self.batch_size = self.config.embedding_batch_size
            self.dimension = self.config.dimensions

            self.index = client.index
            self.embeddings = client.embedding_model
            self.namespace = client.main_namespace

            tracer.DEBUG(
                "__init__",
                "Retriever initialized",
                metadata={
                    "batch_size": self.batch_size,
                    "dimension": self.dimension,
                    "namespace": self.namespace,
                }
            )

        except Exception as e:
            raise RuntimeError(f"Failed to initialize retriever - {str(e)}")

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter_search: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Performs a similarity search for documents matching the given query string by embedding the query 
        and querying the Pinecone index with optional metadata filtering. Returns the top-k most relevant documents.

        Args:
        query (str): The text query string for which similarity search is to be performed.
        k (int): The number of top results to retrieve. Default is 5.
        filter_search (Optional[Dict[str, Any]]): Optional dictionary defining metadata filters to narrow the search.

        Returns:
                List[Dict[str, Any]]: A list of documents represented as dictionaries containing ID, text, metadata, and score.

        Raises:
                ValueError: If the query is empty or k is not greater than zero.
                RuntimeError: If there is a failure generating embeddings or querying Pinecone.
                ValueError: If the filter provided is invalid.
        """
        if not query:
            raise ValueError("The search query cannot be empty.")

        if k <= 0:
            raise ValueError("The parameter k must be greater than zero.")

        try:
            tracer.DEBUG(
                "similarity_search",
                "Generating embedding",
                metadata={"query_preview": query[:50]}
            )

            query_vector = self.embeddings.embed_query(query)

        except Exception as e:
            raise RuntimeError(f"Failed to generate embedding - {str(e)}")

        filter_query: Optional[Dict[str, Any]] = None

        try:
            if filter_search:
                key, value = list(filter_search.items())[0]

                if isinstance(value, list):
                    filter_query = {key: {"$in": value}}
                else:
                    filter_query = {key: {"$eq": value}}

                tracer.DEBUG(
                    "similarity_search",
                    "Filter applied",
                    metadata={"filter": filter_query}
                )

        except Exception as e:
            raise ValueError(f"Invalid filter - {str(e)}")

        try:
            tracer.DEBUG(
                "similarity_search",
                "Querying Pinecone",
                metadata={"k": k, "namespace": self.namespace}
            )

            results = self.index.query(
                vector=query_vector,
                top_k=k,
                namespace=self.namespace,
                include_metadata=True,
                filter=filter_query,
            )

        except Exception as e:
            raise RuntimeError(f"Failure to query Pinecone - {str(e)}")

        documents: List[Dict[str, Any]] = []

        try:
            for match in getattr(results, "matches", []):
                metadata = match.get("metadata", {}).copy()

                document = {
                    "id": match.get("id"),
                    "text": metadata.get("text", ""),
                    "metadata": metadata,
                    "score": match.get("score"),
                }

                document["metadata"].pop("text", None)
                documents.append(document)

            tracer.DEBUG(
                "similarity_search",
                "Results processed",
                metadata={"results_count": len(documents)}
            )

        except Exception as e:
            raise RuntimeError(f"Failed to process search results - {str(e)}")

        return documents

    def get_all_docs_by_metadata(
        self,
        batch_size: int | None = None,
        dimension: int | None = None,
        target_key: str = "file_id",
        target_value: Union[str, List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves all documents from the Pinecone index matching specific metadata values efficiently 
        through paginated queries, allowing filtering by a specified key and accommodating large datasets.

        Args:
        batch_size (int | None): The number of documents to retrieve per batch in pagination. Defaults to the configured batch size.
        dimension (int | None): The embedding dimension to use for the dummy vector in the query. Defaults to configured dimension.
        target_key (str): The metadata key to filter documents by. Default is "file_id".
        target_value (Union[str, List[str]]): The value(s) of the metadata key to match documents against. Cannot be empty.

        Returns:
                List[Dict[str, Any]]: A list of documents represented as dictionaries containing ID, metadata, and score.

        Raises:
                ValueError: If target_value is empty.
                RuntimeError: If there is a failure retrieving data from Pinecone.
        """
        if not target_value:
            raise ValueError("target_value cannot be empty.")

        batch_size = (
            min(batch_size, self.batch_size)
            if batch_size and batch_size > 0
            else self.batch_size
        )

        dimension = (
            dimension if dimension and dimension > 0 else self.dimension
        )

        dummy_vector = [0.0] * dimension

        if isinstance(target_value, list):
            filter_query = {target_key: {"$in": target_value}}
        else:
            filter_query = {target_key: {"$eq": target_value}}

        tracer.DEBUG(
            "get_all_docs_by_metadata",
            "Starting paginated retrieval",
            metadata={
                "target_key": target_key,
                "batch_size": batch_size,
                "namespace": self.namespace,
            }
        )

        results: List[Dict[str, Any]] = []
        pagination_token: Optional[str] = None

        try:
            while True:
                response = self.index.query(
                    vector=dummy_vector,
                    namespace=self.namespace,
                    top_k=batch_size,
                    include_metadata=True,
                    include_values=False,
                    filter=filter_query,
                    pagination_token=pagination_token,
                )

                for match in response.get("matches", []):
                    results.append(
                        {
                            "id": match["id"],
                            "metadata": match.get("metadata", {}),
                            "score": match.get("score"),
                        }
                    )

                pagination_token = (
                    response.get("pagination", {}) or {}
                ).get("next")

                if not pagination_token:
                    break

            tracer.DEBUG(
                "get_all_docs_by_metadata",
                "Retrieval completed",
                metadata={"total_results": len(results)}
            )

        except Exception as e:
            raise RuntimeError(f"Failed to retrieve vectors by target - {str(e)}")

        return results









if __name__ == "__main__":
    import json

    pine_client = PineconeClient(
        index_name="backai-vectorstore",
        main_namespace="betterai-embeddings-dev",
    )

    retriver = PineconeRetriever(pine_client)

    # Similarity search
    similarity_results = retriver.similarity_search(
        query="What is the capital of France?",
        k=5
    )

    print("Similarity Search Results:")
    print(json.dumps(similarity_results, indent=2))

    # Metadata search
    metadata_results = retriver.get_all_docs_by_metadata(
        target_key="file_extension",
        target_value="pdf",
        batch_size=10
    )

    print("\nMetadata Search Results:")
    print(json.dumps(metadata_results, indent=2))

# python -m src.vector_store.pinecone.retriever
```