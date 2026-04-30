import os
from typing import List, Optional, Dict, Any, Union

from src.vector_store.pinecone.pinecone_client import PineconeClient
from src.vector_store.config import PineconeVectorStoreConfig
from src.tracing.tracing_core import ApplicationTracing


tracer = ApplicationTracing(
    flag="PineconeRetriever",
    file_name="pinecone_retriever.py",
    log_file_name="pinecone_module",
    show_info_logs=True
)


class PineconeRetriever:
    def __init__(self, client: Optional[PineconeClient] = None):
        tracer.INFO("__init__", "Initializing retriever")

        try:
            # ==========================
            # Validação / Injeção
            # ==========================
            if not client:
                tracer.DEBUG("__init__", "No client provided, creating default client")
                client = PineconeClient()

            # ==========================
            # Configurações
            # ==========================
            self.config = PineconeVectorStoreConfig()
            self.batch_size = self.config.embedding_batch_size
            self.dimension = self.config.dimensions

            # ==========================
            # Dependências
            # ==========================
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
            tracer.ERROR("__init__", f"Failed to initialize retriever - {str(e)}")
            raise

    # ======================================================
    # Similarity Search
    # ======================================================
    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter_search: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        # ==========================
        # Validações
        # ==========================
        if not query:
            tracer.ERROR("similarity_search", "Empty query received")
            raise ValueError("The search query cannot be empty.")

        if k <= 0:
            tracer.ERROR("similarity_search", "Invalid k value", metadata={"k": k})
            raise ValueError("The parameter k must be greater than zero.")

        # ==========================
        # Embedding
        # ==========================
        try:
            tracer.DEBUG(
                "similarity_search",
                "Generating embedding",
                metadata={"query_preview": query[:50]}
            )

            query_vector = self.embeddings.embed_query(query)

        except Exception as e:
            tracer.ERROR(
                "similarity_search",
                f"Failed to generate embedding - {str(e)}"
            )
            raise RuntimeError("Failed to generate query embedding.") from e

        # ==========================
        # Filtro
        # ==========================
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
            tracer.ERROR(
                "similarity_search",
                f"Invalid filter - {str(e)}",
                metadata={"filter_search": filter_search}
            )
            raise ValueError("Invalid search filter.") from e

        # ==========================
        # Query Pinecone
        # ==========================
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
            tracer.ERROR(
                "similarity_search",
                f"Pinecone query failed - {str(e)}"
            )
            raise RuntimeError("Failure to query Pinecone.") from e

        # ==========================
        # Normalização
        # ==========================
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
            tracer.ERROR(
                "similarity_search",
                f"Failed to process results - {str(e)}"
            )
            raise RuntimeError("Failed to process search results.") from e

        return documents

    # ======================================================
    # Metadata Search
    # ======================================================
    def get_all_docs_by_metadata(
        self,
        batch_size: int | None = None,
        dimension: int | None = None,
        target_key: str = "file_id",
        target_value: Union[str, List[str]] = None,
    ) -> List[Dict[str, Any]]:
        if not target_value:
            tracer.ERROR(
                "get_all_docs_by_metadata",
                "target_value is empty"
            )
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

        # Filtro dinâmico
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
            tracer.ERROR(
                "get_all_docs_by_metadata",
                f"Failed during paginated retrieval - {str(e)}",
                metadata={
                    "target_key": target_key,
                    "target_value": target_value,
                }
            )
            raise RuntimeError(
                "Failed to retrieve vectors by target."
            ) from e

        return results









if __name__ == "__main__":
    import json

    pine_client = PineconeClient(
        index_name="backai-vectorstore",
        main_namespace="embedding_file",
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

# python -m src.vector_store.pinecone.pinecone_retriever