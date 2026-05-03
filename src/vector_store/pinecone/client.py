import os
import logging

from typing import Optional
from dotenv import load_dotenv

import pinecone
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

from src.vector_store.config import PineconeVectorStoreConfig
from src.tracing.tracing_core import ApplicationTracing

load_dotenv()
logging.getLogger("httpx").setLevel(logging.WARNING)

tracer = ApplicationTracing(
    flag="PineconeClient",
    file_name="pinecone_client.py",
    log_file_name="pinecone_module"
)

class PineconeClient:
    """
    Client class to manage connection and operations with Pinecone vector store,
    including initialization of API keys, namespaces, and embedding models.

    Args:
        index_name (str, optional): Pinecone index name to use. Default is None.
        main_namespace (str, optional): Primary namespace for vector storage. Default is None.
        global_namespace (str, optional): Optional global namespace for shared vectors. Default is None.
        embedding_model (str, optional): Name of the OpenAI embedding model to use. Default is None.

    Methods:
        get_namespace(): Resolves and returns the namespace to use for vector operations.
        create_vector_store(): Creates and returns a PineconeVectorStore for vector operations.
    """
    def __init__(
        self,
        index_name: Optional[str] = None,
        main_namespace: Optional[str] = None,
        global_namespace: Optional[str] = None,
        embedding_model: Optional[str] = None,
    ):
        tracer.INFO("__init__", "Initializing client")

        try:
            self.openai_key = os.getenv("OPENAI_API_KEY")
            self.pinecone_key = os.getenv("PINECONE_API_KEY")
            self.config = PineconeVectorStoreConfig()

            if not self.openai_key or not self.pinecone_key:
                raise EnvironmentError(
                    "OPENAI_API_KEY or PINECONE_API_KEY not found."
                )

            self.index_name = (
                index_name
                or os.getenv("PINECONE_INDEX_NAME", self.config.index_name)
            )

            if not self.index_name:
                raise ValueError(
                    "index_name not provided or defined in PINECONE_INDEX_NAME."
                )

            self.main_namespace = (
                main_namespace
                or os.getenv("PINECONE_NAMESPACE", self.config.namespace)
            )

            self.global_namespace = (
                global_namespace
                or os.getenv(
                    "PINECONE_GLOBAL_NAMESPACE",
                    self.config.global_namespace
                )
            )

            self.embedding_model_name = (
                embedding_model
                or os.getenv(
                    "OPENAI_EMBEDDING_MODEL",
                    self.config.embedding_model
                )
            )

            tracer.DEBUG(
                "__init__",
                "Client parameters resolved",
                metadata={
                    "index_name": self.index_name,
                    "main_namespace": self.main_namespace,
                    "global_namespace": self.global_namespace,
                    "embedding_model": self.embedding_model_name,
                }
            )

            self._init_pinecone()
            self._init_embeddings()

        except Exception as e:
            raise RuntimeError(f"Failed to initialize PineconeClient: {str(e)}")

    def _init_pinecone(self) -> None:
        """
        Initializes the connection to the Pinecone service, setting up the client and index.
        """
        tracer.DEBUG("_init_pinecone", "Connecting to Pinecone")

        self.pc = pinecone.Pinecone(api_key=self.pinecone_key)
        self.index = self.pc.Index(self.index_name)

        tracer.DEBUG(
            "_init_pinecone",
            "Pinecone connection established",
            metadata={"index_name": self.index_name}
        )

    def _init_embeddings(self, model_name: Optional[str] = None) -> None:
        """
        Initializes the OpenAI embedding model to be used for vector operations.

        Args:
            model_name (str, optional): Name of the embedding model to initialize. Defaults to the client's embedding model name.
        """
        model = model_name or self.embedding_model_name

        tracer.DEBUG(
            "_init_embeddings",
            "Initializing embeddings model",
            metadata={"model": model}
        )

        self.embedding_model = OpenAIEmbeddings(model=model)

    def get_namespace(self, namespace: Optional[str] = None) -> str:
        """
        Resolves and returns the namespace to use, defaulting to the main namespace if none provided.

        Args:
            namespace (str, optional): Namespace override. Default is None.

        Returns:
            str: The resolved namespace string.
        """
        resolved = namespace or self.main_namespace

        tracer.DEBUG(
            "get_namespace",
            "Namespace resolved",
            metadata={
                "input": namespace,
                "resolved": resolved
            }
        )

        return resolved

    def create_vector_store(
        self,
        namespace: Optional[str] = None,
        embedding_model: Optional[OpenAIEmbeddings] = None,
    ) -> PineconeVectorStore:
        """
        Creates and returns a PineconeVectorStore instance configured with the specified or default namespace and embedding model.

        Args:
            namespace (str, optional): Namespace to use for the vector store. Default is None.
            embedding_model (OpenAIEmbeddings, optional): Embedding model to use. Defaults to the client's embedding model.

        Returns:
            PineconeVectorStore: Configured vector store instance ready for operations.
        """
        resolved_namespace = self.get_namespace(namespace)

        tracer.DEBUG(
            "create_vector_store",
            "Creating vector store",
            metadata={"namespace": resolved_namespace}
        )

        vector_store = PineconeVectorStore(
            index=self.index,
            embedding=embedding_model or self.embedding_model,
            text_key="text",
            namespace=resolved_namespace,
        )

        return vector_store
