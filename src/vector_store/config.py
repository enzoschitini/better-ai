from enum import Enum


class VectorStoreProvider(str, Enum):
    PINECONE = "pinecone"
    OPENSEARCH = "opensearch"

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"