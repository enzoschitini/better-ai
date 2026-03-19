import os
import logging
from typing import Optional

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
import pinecone
from langchain_pinecone import PineconeVectorStore


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

        if not self.openai_key or not self.pinecone_key:
            raise EnvironmentError(
                "OPENAI_API_KEY ou PINECONE_API_KEY não encontrados."
            )

        # ======================================================
        # Configurações
        # ======================================================
        self.index_name = index_name or os.getenv("PINECONE_INDEX_NAME")
        if not self.index_name:
            raise ValueError(
                "index_name não informado nem definido em PINECONE_INDEX_NAME."
            )

        self.main_namespace = (
            main_namespace or os.getenv("PINECONE_NAMESPACE", "default")
        )

        self.global_namespace = (
            global_namespace
            or os.getenv("PINECONE_GLOBAL_NAMESPACE", "global")
        )

        self.embedding_model_name = (
            embedding_model
            or os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")
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
        self.embeddings = OpenAIEmbeddings(
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
        embeddings: Optional[OpenAIEmbeddings] = None,
    ) -> PineconeVectorStore:
        """
        Cria um VectorStore para ingestão ou busca.
        """
        return PineconeVectorStore(
            index=self.index,
            embedding=embeddings or self.embeddings,
            text_key="text",
            namespace=self.get_namespace(namespace),
        )
