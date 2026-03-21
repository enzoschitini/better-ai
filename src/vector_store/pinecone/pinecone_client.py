import os
from typing import Optional

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
import pinecone
from langchain_pinecone import PineconeVectorStore

from src.vector_store.config import PineconeVectorStoreConfig
from src.tracing.tracing_core import ApplicationTracing

load_dotenv()

tracer = ApplicationTracing(
    flag="PineconeClient",
    file_name="pinecone_client.py",
    log_file_name="pinecone_module"
)


def trace(method_name: str):
    """
    Decorator para padronizar logging e captura de erros.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer.INFO(method_name, "Execution started")
            try:
                result = func(*args, **kwargs)
                tracer.INFO(method_name, "Execution finished successfully")
                return result
            except Exception as e:
                tracer.ERROR(
                    method_name,
                    "Execution failed",
                    error=e
                )
                raise
        return wrapper
    return decorator


class PineconeClient:
    """
    Cliente unificado responsável por:
    - Carregar credenciais
    - Inicializar Pinecone
    - Inicializar embeddings
    - Criar VectorStores
    - Criar Retrievers
    - Gerenciar namespaces
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
            # ======================================================
            # Credenciais
            # ======================================================
            self.openai_key = os.getenv("OPENAI_API_KEY")
            self.pinecone_key = os.getenv("PINECONE_API_KEY")
            self.config = PineconeVectorStoreConfig()

            if not self.openai_key or not self.pinecone_key:
                tracer.ERROR(
                    "__init__",
                    "Missing API keys",
                    metadata={
                        "openai_key_exists": bool(self.openai_key),
                        "pinecone_key_exists": bool(self.pinecone_key),
                    }
                )
                raise EnvironmentError(
                    "OPENAI_API_KEY or PINECONE_API_KEY not found."
                )

            # ======================================================
            # Configurações
            # ======================================================
            self.index_name = (
                index_name
                or os.getenv("PINECONE_INDEX_NAME", self.config.index_name)
            )

            if not self.index_name:
                tracer.ERROR(
                    "__init__",
                    "Index name not provided",
                )
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

            # ======================================================
            # Inicializações
            # ======================================================
            self._init_pinecone()
            self._init_embeddings()

        except Exception as e:
            tracer.ERROR("__init__", "Client initialization failed", error=e)
            raise

    # ======================================================
    # Internals
    # ======================================================

    @trace("_init_pinecone")
    def _init_pinecone(self) -> None:
        tracer.DEBUG("_init_pinecone", "Connecting to Pinecone")

        self.pc = pinecone.Pinecone(api_key=self.pinecone_key)
        self.index = self.pc.Index(self.index_name)

        tracer.DEBUG(
            "_init_pinecone",
            "Pinecone connection established",
            metadata={"index_name": self.index_name}
        )

    @trace("_init_embeddings")
    def _init_embeddings(self, model_name: Optional[str] = None) -> None:
        model = model_name or self.embedding_model_name

        tracer.DEBUG(
            "_init_embeddings",
            "Initializing embeddings model",
            metadata={"model": model}
        )

        self.embedding_model = OpenAIEmbeddings(model=model)

    # ======================================================
    # Public API
    # ======================================================

    def get_namespace(self, namespace: Optional[str] = None) -> str:
        """
        Resolve namespace padrão.
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

    @trace("create_vector_store")
    def create_vector_store(
        self,
        namespace: Optional[str] = None,
        embedding_model: Optional[OpenAIEmbeddings] = None,
    ) -> PineconeVectorStore:
        """
        Cria um VectorStore para ingestão ou busca.
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