import logging
from typing import List, Dict, Any, Optional

from src.vector_store.pinecone_client import PineconeClient

logger = logging.getLogger(__name__)


class PineconeRetriever:
    """
    Recuperação direta de vetores via file_id usando filtro por metadata.
    """

    def __init__(self, client: PineconeClient):
        if not client:
            raise ValueError("PineconeClient cannot be None.")

        self.index = client.index
        self.namespace = client.namespace

    def get_by_file_id(
        self,
        file_id: str,
        batch_size: int = 100,
    ) -> List[Dict[str, Any]]:

        if not file_id:
            raise ValueError("file_id cannot be empty.")

        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero.")

        # 🔑 Dummy vector (exigência do Pinecone)
        dummy_vector = [0.0] * 3072

        results: List[Dict[str, Any]] = []
        pagination_token: Optional[str] = None

        try:
            while True:
                response = self.index.query(
                    vector=dummy_vector,  # ✅ obrigatório
                    namespace=self.namespace,
                    top_k=batch_size,
                    include_metadata=True,
                    include_values=False,
                    filter={
                        "file_id": {"$eq": file_id}
                    },
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

        except Exception as e:
            logger.exception(
                "Failed to retrieve vectors for file_id=%s", file_id
            )
            raise RuntimeError(
                "Failed to retrieve vectors by file_id."
            ) from e

        return results




import json

client = PineconeClient(
    namespace="betterai-embeddings-dev",
    embedding_model="text-embedding-3-large"
)

retriever = PineconeRetriever(client)

vectors = retriever.get_by_file_id("21d75dca2eec7b02080327f40220e20dxx2")

print(len(vectors))

#print(f"\n\n{json.dumps(vectors, indent=4)}\n\n")

# python -m src.vector_store.all