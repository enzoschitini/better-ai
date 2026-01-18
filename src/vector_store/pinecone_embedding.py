import os
from datetime import datetime, timezone
from typing import List, Dict, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.embeddings import OpenAIEmbeddings

from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

from src.vector_store.pinecone_client import PineconeClient
from dotenv import load_dotenv

load_dotenv()







# ============================================================
# ===================== TEXT CHUNKING ========================
# ============================================================

class TextChunker:
    """Responsável apenas por dividir texto em chunks."""

    def __init__(self, chunk_size: int = 3000, chunk_overlap: int = 300):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", " "]
        )

    def split(self, text: str) -> List[str]:
        return self.splitter.split_text(text)


# ============================================================
# ==================== DOCUMENT FACTORY ======================
# ============================================================

class DocumentFactory:
    """Cria objetos Document a partir de chunks."""

    @staticmethod
    def from_chunks(chunks: List[str], metadata: Dict) -> List[Document]:
        return [
            Document(page_content=chunk, metadata=dict(metadata))
            for chunk in chunks
        ]


# ============================================================
# ================== PINECONE REPOSITORY =====================
# ============================================================

class PineconeRepository:
    """
    Camada de infraestrutura.
    Responsável apenas por interagir com o Pinecone.
    """

    def __init__(self, client, embeddings, dimensions: int):
        self.client = client
        self.embeddings = embeddings
        self.dimensions = dimensions

    def vector_store(self, namespace: str):
        return self.client.create_vector_store(
            embeddings=self.embeddings,
            namespace=namespace
        )

    def delete_by_metadata(
        self,
        feature: str,
        value: str,
        namespace: str
    ) -> int:
        results = self.client.index.query(
            vector=[0.0] * self.dimensions,
            namespace=namespace,
            filter={feature: {"$eq": value}},
            top_k=10000,
        )

        ids = [match["id"] for match in results.get("matches", [])]

        for i in range(0, len(ids), 1000):
            self.client.index.delete(
                ids=ids[i:i + 1000],
                namespace=namespace
            )

        return len(ids)


# ============================================================
# ================= VECTOR INGESTION SERVICE =================
# ============================================================

class VectorIngestionService:
    """
    Orquestra:
    - chunking
    - criação de documentos
    - persistência no Pinecone
    """

    def __init__(
        self,
        repository: PineconeRepository,
        chunker: TextChunker,
        document_factory: DocumentFactory,
        main_namespace: str,
        global_namespace: str,
    ):
        self.repo = repository
        self.chunker = chunker
        self.document_factory = document_factory
        self.main_namespace = main_namespace
        self.global_namespace = global_namespace

    def ingest(
        self,
        text: str,
        metadata: Dict,
        save_global: bool = False,
        batch_size: int = 100
    ) -> Dict:

        if batch_size > 100:
            batch_size = 100

        dt_utc = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)
        metadata["created_at"] = str(dt_utc)

        chunks = self.chunker.split(text)
        documents = self.document_factory.from_chunks(chunks, metadata)

        main_store = self.repo.vector_store(self.main_namespace)
        global_store = self.repo.vector_store(self.global_namespace)

        saved_ids = []
        batch_number = 0

        try:
            for i in range(0, len(documents), batch_size):
                batch_number += 1
                batch_docs = documents[i:i + batch_size]

                ids = main_store.add_documents(batch_docs)
                saved_ids.extend(ids)

                if save_global:
                    global_store.add_documents(batch_docs)

        except Exception as error:
            # rollback defensivo
            self.repo.delete_by_metadata(
                "file_id",
                metadata.get("file_id"),
                self.main_namespace
            )

            if save_global:
                self.repo.delete_by_metadata(
                    "file_id",
                    metadata.get("file_id"),
                    self.global_namespace
                )

            return {
                "status": "error",
                "message": "Erro ao salvar embeddings no Pinecone.",
                "error": str(error),
                "saved_ids": saved_ids,
                "batch": batch_number
            }

        return {
            "status": "success",
            "message": "Embeddings salvos com sucesso.",
            "chunks": len(documents),
            "batches": batch_number,
            "ids": saved_ids,
            "namespace_main": self.main_namespace,
            "namespace_global": self.global_namespace if save_global else None
        }



# ============================================================
# ===================== MAIN FACADE ==========================
# ============================================================

class PineconeVectorService:
    """
    Facade pública.
    Mantém compatibilidade com sua implementação atual.
    """

    def __init__(
        self,
        vector_client,
        embedding_model_name: Optional[str] = None,
        dimensions: Optional[int] = None,
    ):
        self.client = vector_client

        self.embeddings = OpenAIEmbeddings(
            model=embedding_model_name
            or os.getenv(
                "KNOWLEDGE_BASE_EMBEDDINGS_MODEL",
                "text-embedding-3-small"
            )
        )

        self.dimensions = dimensions or 1536

        self.repository = PineconeRepository(
            client=self.client,
            embeddings=self.embeddings,
            dimensions=self.dimensions
        )

        self.chunker = TextChunker()
        self.document_factory = DocumentFactory()

        self.ingestion_service = VectorIngestionService(
            repository=self.repository,
            chunker=self.chunker,
            document_factory=self.document_factory,
            main_namespace=self.client.main_namespace,
            global_namespace=self.client.global_namespace
        )

    # ----------------- API pública -----------------

    def generate_vectors(
        self,
        text: str,
        metadata: Dict,
        save_global: bool = False,
        batch_size: int = 100
    ):
        return self.ingestion_service.ingest(
            text=text,
            metadata=metadata,
            save_global=save_global,
            batch_size=batch_size
        )

    def delete_documents(
        self,
        target_feature: str,
        target_id: str,
        namespace: str
    ):
        deleted = self.repository.delete_by_metadata(
            feature=target_feature,
            value=target_id,
            namespace=namespace
        )

        if deleted:
            return {
                "deleted_vectors": deleted,
                "message": f"✅ {deleted} vetores apagados de `{namespace}`"
            }

        return f"Nenhum vetor encontrado em `{namespace}`"






pinecone_client = PineconeClient(
    index_name="backai-vectorstore",
    main_namespace="test_namespace",
)

vector_service = PineconeVectorService(
    vector_client=pinecone_client,  # seu client já existente
    embedding_model_name="text-embedding-3-large",  # opcional
    dimensions=3072                                 # opcional
)

text = """
Python é uma linguagem de programação de alto nível,
muito usada em ciência de dados, automação e IA.
"""

metadata = {
    "file_id": "doc_001",
    "source": "manual_python",
    "type": "knowledge_base"
}

response = vector_service.generate_vectors(
    text=text,
    metadata=metadata,
    save_global=False,   # salva também no namespace global
    batch_size=50
)

print(response)











# python -m src.vector_store.pinecone_vector_store