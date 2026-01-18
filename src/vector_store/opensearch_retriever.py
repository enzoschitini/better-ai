"""
Docstring per vector_store.opensearch_retriever

from typing import Optional, List, Dict, Any
import logging
from langchain_openai import OpenAIEmbeddings
from opensearchpy import OpenSearchException
from src.vector_store.config import DEFAULT_EMBEDDING_MODEL
from src.vector_store.opensearch_client import OpenSearchClient

logger = logging.getLogger(__name__)


class OpenSearchRetriever:
    def __init__(
        self,
        client: OpenSearchClient,
        embedding_model_name: Optional[str] = None,
    ):
        self.opensearch_client = client
        self.embedding_model = OpenAIEmbeddings(
            model=embedding_model_name or DEFAULT_EMBEDDING_MODEL
        )

    def embed_query(self, query: str) -> List[float]:
        return self.embedding_model.embed_query(query)

    def build_knn_query(
        self,
        query_emb: List[float],
        k: int,
        filter_search: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        knn_query = {"knn": {"embedding": {"vector": query_emb, "k": k}}}
        filter_clauses = [
            (
                {"terms": {f"metadata.{key}": value}}
                if isinstance(value, list)
                else {"term": {f"metadata.{key}": value}}
            )
            for key, value in (filter_search or {}).items()
        ]
        if filter_clauses:
            return {
                "size": k,
                "query": {"bool": {"must": [knn_query], "filter": filter_clauses}},
            }
        return {"size": k, "query": knn_query}

    def similarity_search(
        self,
        query: str,
        index_name: str,
        k: int = 3,
        filter_search: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        try:
            query_emb = self.embed_query(query)
            body = self.build_knn_query(query_emb, k, filter_search)
            resp = self.opensearch_client.client.search(index=index_name, body=body)
            hits = resp.get("hits", {}).get("hits", [])
            results = []
            for hit in hits:
                source = hit.get("_source", {}).copy()
                source.pop("embedding", None)
                result = {
                    "id": hit.get("_id"),
                    **source,
                    "score": hit.get("_score"),
                }
                results.append(result)
            return results
        except (OpenSearchException, ValueError, KeyError) as e:
            logger.error("Error during document search: %s", e)
            return []

"""