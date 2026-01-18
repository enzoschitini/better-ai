import logging
from typing import List, Optional, Dict, Any

from src.vector_store.pinecone_client import PineconeClient

logger = logging.getLogger(__name__)

class PineconeRetriever:
    """
    Serviço responsável exclusivamente por operações
    de busca por similaridade no Pinecone.
    """

    def __init__(self, client: PineconeClient):
        # Validação
        if not client:
            logger.error("PineconeClient cannot be None.")
            raise ValueError("PineconeClient cannot be None.")

        self.index = client.index
        self.embeddings = client.embeddings
        self.namespace = client.namespace

    def similarity_search(
        self, query: str, k: int = 5, filter_search: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Realiza busca por similaridade no Pinecone.

        :param query: Texto de consulta.
        :param k: Número de resultados retornados.
        :param filter_search: Filtro opcional para a busca.
        :return: Lista de documentos similares.
        """

        # Evita chamadas desnecessárias ao Pinecone
        if not query:
            logger.error("The search query cannot be empty.")
            raise ValueError("The search query cannot be empty.")

        if k <= 0:
            logger.error("The parameter k must be greater than zero.")
            raise ValueError("The parameter k must be greater than zero.")

        try:
            # Geração do embedding da query
            query_vector = self.embeddings.embed_query(query)

        except Exception as e:
            logger.exception("Failed to generate query embedding.")
            raise RuntimeError("Failed to generate query embedding.") from e

        filter_query: Optional[Dict[str, Any]] = None

        try:
            # Suporte a filtros simples com $eq ou listas com $in
            if filter_search:
                key, value = list(filter_search.items())[0]

                if isinstance(value, list):
                    filter_query = {key: {"$in": value}}
                else:
                    filter_query = {key: {"$eq": value}}

        except Exception as e:
            logger.exception("Invalid search filter: %r", filter_search)
            raise ValueError("Invalid search filter.") from e

        try:
            # Consulta direta ao índice do Pinecone
            results = self.index.query(
                vector=query_vector,
                top_k=k,
                namespace=self.namespace,
                include_metadata=True,
                filter=filter_query,
            )

        except Exception as e:
            logger.exception("Failure to query Pinecone.")
            raise RuntimeError("Failure to query Pinecone.") from e

        documents: List[Dict[str, Any]] = []

        try:
            # Normalização da resposta para o formato interno da aplicação
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

        except Exception as e:
            logger.exception("Failed to process search results.")
            raise RuntimeError("Failed to process search results.") from e

        return documents