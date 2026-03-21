import os
import logging
from typing import Optional

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
import pinecone
from langchain_pinecone import PineconeVectorStore
from src.vector_store.config import PineconeVectorStoreConfig


load_dotenv()

logger = logging.getLogger(__name__)

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
        # ======================================================
        # Credenciais
        # ======================================================
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.pinecone_key = os.getenv("PINECONE_API_KEY")
        self.config = PineconeVectorStoreConfig()

        if not self.openai_key or not self.pinecone_key:
            raise EnvironmentError(
                "OPENAI_API_KEY or PINECONE_API_KEY not found."
            )

        # ======================================================
        # Configurações
        # ======================================================
        self.index_name = index_name or os.getenv("PINECONE_INDEX_NAME", self.config.index_name)
        if not self.index_name:
            raise ValueError(
                "index_name not provided or defined in PINECONE_INDEX_NAME."
            )

        self.main_namespace = (
            main_namespace or os.getenv("PINECONE_NAMESPACE", self.config.namespace)
        )

        self.global_namespace = (
            global_namespace
            or os.getenv("PINECONE_GLOBAL_NAMESPACE", self.config.global_namespace)
        )

        self.embedding_model_name = (
            embedding_model
            or os.getenv("OPENAI_EMBEDDING_MODEL", self.config.embedding_model)
        )

        # ======================================================
        # Inicializações
        # ======================================================
        self._init_pinecone()
        self._init_embeddings()

    # ======================================================
    # Internals
    # ======================================================

    def _init_pinecone(self) -> None:
        self.pc = pinecone.Pinecone(api_key=self.pinecone_key)
        self.index = self.pc.Index(self.index_name)

    def _init_embeddings(self, model_name: Optional[str] = None) -> None:
        self.embedding_model = OpenAIEmbeddings(
            model=model_name or self.embedding_model_name
        )

    # ======================================================
    # Public API
    # ======================================================

    def get_namespace(self, namespace: Optional[str] = None) -> str:
        """
        Resolve namespace padrão.
        """
        return namespace or self.main_namespace

    def create_vector_store(
        self,
        namespace: Optional[str] = None,
        embedding_model: Optional[OpenAIEmbeddings] = None,
    ) -> PineconeVectorStore:
        """
        Cria um VectorStore para ingestão ou busca.
        """
        return PineconeVectorStore(
            index=self.index,
            embedding=embedding_model or self.embedding_model,
            text_key="text",
            namespace=self.get_namespace(namespace),
        )
