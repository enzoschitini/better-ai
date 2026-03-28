```python
import os
from typing import List, Optional, Dict, Any

from dotenv import load_dotenv
from datetime import datetime, timezone

from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from src.vector_store.pinecone.pinecone_client import PineconeClient
from src.vector_store.config import PineconeVectorStoreConfig
from src.tracing.tracing_core import ApplicationTracing

load_dotenv()


tracer = ApplicationTracing(
    flag="PineconeVectorService",
    file_name="pinecone_vector_service.py",
    log_file_name="pinecone_module"
)


def trace(method_name: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer.INFO(method_name, "Execution started")
            try:
                result = func(*args, **kwargs)
                tracer.INFO(method_name, "Execution finished successfully")
                return result
            except Exception as e:
                tracer.ERROR(method_name, "Execution failed", error=e)
                raise
        return wrapper
    return decorator


class PineconeVectorService:
    """
    Service responsável por:
    - transformar texto em chunks
    - gerar embeddings
    - salvar nos namespaces

    Args:
    :param vector_client (Optional[PineconeClient]): Cliente Pinecone opcional para comunicação com o serviço de vetor. Default é None.
    :param embedding_model_name (str): Nome do modelo de embedding utilizado para gerar embeddings. Default é None.
    :param dimensions (int): Número de dimensões dos vetores de embedding. Default é None.

    Methods:
            generate_vectors(text, metadata, save_global=False, batch_size=None): Gera e armazena embeddings para o texto dado.
    """

    def __init__(
        self,
        vector_client: Optional[PineconeClient] = None,
        embedding_model_name: str = None,
        dimensions: int = None
    ):
        tracer.INFO("__init__", "Initializing vector service")

        try:
            if not vector_client:
                tracer.DEBUG("__init__", "No client provided, creating default")
                vector_client = PineconeClient()

            self.client = vector_client
            self.config = PineconeVectorStoreConfig()

            # Configs
            self.chunk_size = self.config.chunk_size
            self.chunk_overlap = self.config.chunk_overlap
            self.separators = self.config.separators
            self.namespace = self.config.namespace
            self.top_k = self.config.top_k
            self.delete_batch_size = self.config.delete_batch_size
            self.embedding_batch_size = self.config.embedding_batch_size

            # Embeddings
            self.embeddings_model = OpenAIEmbeddings(
                model=embedding_model_name or os.getenv(
                    "OPENAI_EMBEDDING_MODEL",
                    self.config.embedding_model
                )
            )

            self.dimensions = dimensions or self.config.dimensions

            # Vector stores
            self.global_vectordb = self.client.create_vector_store(
                embedding_model=self.embeddings_model,
                namespace=self.client.global_namespace
            )

            self.main_vectordb = self.client.create_vector_store(
                embedding_model=self.embeddings_model,
                namespace=self.client.main_namespace
            )

            tracer.DEBUG(
                "__init__",
                "Vector service initialized",
                metadata={
                    # Configurações de chunking
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap,
                    "separators": self.separators,

                    # Configurações de busca / controle
                    "top_k": self.top_k,
                    "delete_batch_size": self.delete_batch_size,
                    "embedding_batch_size": self.embedding_batch_size,

                    # Embeddings
                    "embedding_model": embedding_model_name or os.getenv(
                        "OPENAI_EMBEDDING_MODEL",
                        self.config.embedding_model
                    ),

                    # Estrutura vetorial
                    "dimensions": self.dimensions,

                    # Namespaces
                    "main_namespace": self.client.main_namespace,
                    "global_namespace": self.client.global_namespace,

                    # Infra
                    "index_name": getattr(self.client, "index_name", None),

                    # Flags implícitas
                    "has_custom_client": vector_client is not None,
                }
            )

        except Exception as e:
            tracer.ERROR("__init__", "Initialization failed", error=e)
            raise

    # ======================================================
    # Helpers
    # ======================================================

    @trace("split_text")
    def split_text(
        self,
        text: str,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> List[str]:
        """
        Divide o texto de entrada em pedaços menores (chunks) com tamanho e sobreposição especificados,
        utilizando separadores definidos.

        Args: 
        text (str): O texto completo que será dividido em chunks.
        chunk_size (int | None): Tamanho máximo de cada chunk. Default é None, que usa o valor configurado na instância.
        chunk_overlap (int | None): Quantidade de sobreposição entre chunks consecutivos. Default é None, que usa o valor configurado na instância.

        Returns:
                List[str]: Lista de strings contendo os chunks gerados do texto original.
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size or self.chunk_size,
            chunk_overlap=chunk_overlap or self.chunk_overlap,
            separators=self.separators,
        )

        chunks = splitter.split_text(text)

        tracer.DEBUG(
            "split_text",
            "Text split into chunks",
            metadata={"chunks": len(chunks)}
        )

        return chunks

    @staticmethod
    def build_documents(chunks: List[str], metadata: Dict[str, Any]) -> List[Document]:
        return [
            Document(page_content=chunk, metadata={**metadata})
            for chunk in chunks
        ]

    @trace("delete_documents")
    def delete_documents(
        self,
        target_feature: str,
        target_id: str,
        namespace: str
    ):
        """
        Remove documentos do vetor armazenado no namespace especificado, cujo metadado corresponde
        ao filtro definido pelo par target_feature e target_id.

        Args: 
        target_feature (str): A chave do campo de metadado pelo qual filtrar os documentos a deletar.
        target_id (str): O valor do campo de metadado que identificar os documentos a serem removidos.
        namespace (str): Namespace onde a deleção será executada.

        Returns:
                dict: Dicionário com a quantidade de vetores deletados e o namespace usado.
        """
        namespace = namespace or self.namespace

        tracer.DEBUG(
            "delete_documents",
            "Input metadata",
            metadata={
                "target_feature": target_feature,
                "target_id": target_id,
                "namespace": namespace,
            }
        )

        try:
            results = self.client.index.query(
                vector=[0.0] * self.dimensions,
                namespace=namespace,
                filter={target_feature: {"$eq": target_id}},
                top_k=self.top_k,
            )

            ids_to_delete = [
                match["id"] for match in results.get("matches", [])
            ]

            if ids_to_delete:
                for i in range(0, len(ids_to_delete), self.delete_batch_size):
                    batch = ids_to_delete[i:i + self.delete_batch_size]
                    self.client.index.delete(ids=batch, namespace=namespace)

                tracer.DEBUG(
                    "delete_documents",
                    "Vectors deleted",
                    metadata={
                        "count": len(ids_to_delete),
                        "namespace": namespace
                    }
                )

                return {
                    "deleted_vectors": len(ids_to_delete),
                    "namespace": namespace
                }

            tracer.DEBUG(
                "delete_documents",
                "No vectors found",
                metadata={"namespace": namespace}
            )

            return {"deleted_vectors": 0}

        except Exception as e:
            tracer.ERROR(
                "delete_documents",
                "Deletion failed",
                metadata={
                    "target_feature": target_feature,
                    "target_id": target_id,
                },
                error=e
            )
            raise

    # ======================================================
    # Search
    # ======================================================

    @trace("document_search")
    def document_search(
        self,
        query: str,
        k: int = 3,
        namespace: str = None,
        filter: dict = None,
    ):
        """
        Executa uma busca por similaridade no vetor com base na consulta fornecida,
        retornando os documentos mais relevantes no namespace informado.

        Args:
        query (str): Texto da consulta para busca por similaridade.
        k (int): Quantidade máxima de resultados a retornar. Default é 3.
        namespace (str): Namespace onde será realizada a busca. Default é None, usa o namespace principal.
        filter (dict): Filtros opcionais para restringir a busca.

        Returns:
                dict: Dicionário formatado com os resultados da busca, contendo IDs e metadados.
        """
        selected_namespace = namespace or self.client.main_namespace

        vectordb = self.client.create_vector_store(
            embedding_model=self.embeddings_model,
            namespace=selected_namespace
        )

        try:
            results = vectordb.similarity_search(
                query=query,
                k=k,
                filter=filter
            )

            formatted = {}

            for r in results:
                formatted[r.id] = {
                    "metadata": r.metadata,
                    "page_content": r.page_content
                }

            tracer.DEBUG(
                "document_search",
                "Search completed",
                metadata={"results_count": len(formatted)}
            )

            return formatted

        except Exception as e:
            tracer.ERROR(
                "document_search",
                "Search failed",
                error=e
            )
            raise RuntimeError("Document search failed.") from e

    # ======================================================
    # Embeddings
    # ======================================================

    @trace("generate_vectors")
    def generate_vectors(
        self,
        text: str,
        metadata: dict,
        save_global: bool = False,
        batch_size: int | None = None,
    ):
        """
        Gera embeddings para o texto informado, divide o texto em chunks, cria documentos e armazena os vetores no namespace principal.
        Opcionalmente, salva também na base global e executa rollback em caso de erro.

        Args:
        text (str): O texto completo para geração de embeddings.
        metadata (dict): Metadados associados que serão adicionados a cada vetor.
        save_global (bool): Indica se deve salvar também na base global. Default é False.
        batch_size (int | None): Tamanho opcional dos batches para adição dos documentos. Default é None, utiliza configuração padrão.

        Returns:
                dict: Dicionário contendo status, mensagem e informações sobre os embeddings gerados.
        """
        dt_utc = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)
        metadata["created_at"] = str(dt_utc)

        chunks = self.split_text(text)
        documents = self.build_documents(chunks, metadata)

        batch_size = (
            min(batch_size, self.embedding_batch_size)
            if batch_size and batch_size > 0
            else self.embedding_batch_size
        )

        all_ids = []
        batch_number = 0

        try:
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i: i + batch_size]
                batch_number += 1

                tracer.DEBUG(
                    "generate_vectors",
                    "Processing batch",
                    metadata={
                        "batch_number": batch_number,
                        "batch_size": len(batch_docs)
                    }
                )

                ids = self.main_vectordb.add_documents(batch_docs)
                all_ids.extend(ids)

                if save_global:
                    self.global_vectordb.add_documents(batch_docs)

        except Exception as error:
            tracer.ERROR(
                "generate_vectors",
                "Batch failed, starting rollback",
                metadata={"batch_number": batch_number},
                error=error
            )

            # rollback
            self.delete_documents(
                "file_id",
                metadata.get("file_id"),
                self.client.main_namespace
            )

            if save_global:
                self.delete_documents(
                    "file_id",
                    metadata.get("file_id"),
                    self.client.global_namespace
                )

            return {
                "status": "error",
                "message": "Error saving embeddings in Pinecone.",
                "error": str(error),
                "saved_ids": all_ids,
                "batch": batch_number
            }

        response = {
            "status": "success",
            "message": "Embeddings saved successfully.",
            "embedding_informations": {
                "namespace_main": self.client.main_namespace,
                "namespace_global": self.client.global_namespace if save_global else None,
                "batch_count": batch_number,
                "chunks_ids": all_ids
            }
        }

        tracer.DEBUG(
            "generate_vectors",
            "All batches processed",
            metadata={
                "total_batches": batch_number,
                "total_vectors": len(all_ids),
                "response": response,
            }
        )

        return response
```