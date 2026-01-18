import os
import logging
from typing import Optional

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
import pinecone

load_dotenv()

logger = logging.getLogger(__name__)

class PineconeClient:
    """
    Cliente responsável por:
    - Carregar credenciais
    - Inicializar Pinecone
    - Inicializar embeddings
    """

    def __init__(
        self,
        index_name: Optional[str] = None,
        namespace: Optional[str] = None,
        embedding_model: Optional[str] = None
    ):
        # Carrega credenciais obrigatórias
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.pinecone_key = os.getenv("PINECONE_API_KEY")

        if not self.openai_key or not self.pinecone_key:
            logger.error("Credenciais OPENAI_API_KEY ou PINECONE_API_KEY não encontradas.")
            raise EnvironmentError(
                "Credenciais OPENAI_API_KEY ou PINECONE_API_KEY não encontradas."
            )

        # Prioridade: parâmetro > variável de ambiente
        self.index_name = index_name or os.getenv("PINECONE_INDEX_NAME")
        self.namespace = namespace or os.getenv("KNOWLEDGE_BASE_PINECONE")
        self.embedding_model = (
            embedding_model
            or os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        )

        if not self.index_name:
            logger.error("index_name não informado nem encontrado na variável de ambiente PINECONE_INDEX_NAME.")
            raise ValueError(
                "index_name não informado nem encontrado na variável de ambiente PINECONE_INDEX_NAME."
            )

        self._init_pinecone()
        self._init_embeddings(self.embedding_model)

    def _init_pinecone(self) -> None:
        """Inicializa o cliente e o índice Pinecone."""
        self.pc = pinecone.Pinecone(api_key=self.pinecone_key)
        self.index = self.pc.Index(self.index_name)

    def _init_embeddings(self, model_name: str) -> None:
        """Inicializa o modelo de embeddings."""
        self.embeddings = OpenAIEmbeddings(model=model_name)