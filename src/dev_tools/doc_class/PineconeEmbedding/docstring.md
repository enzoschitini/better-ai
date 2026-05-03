```python
import os
import logging

from dotenv import load_dotenv
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

from src.vector_store.pinecone.client import PineconeClient
from src.vector_store.config import PineconeVectorStoreConfig
from src.tracing.tracing_core import ApplicationTracing

load_dotenv()
logging.getLogger("httpx").setLevel(logging.WARNING)

tracer = ApplicationTracing(
    flag="PineconeEmbedding",
    file_name="pinecone_vector_service.py",
    log_file_name="pinecone_module"
)

class EmbeddingHelpers:
    def split_text(
        self,
        text: str,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> List[str]:
        """
        Splits the provided text into chunks using a recursive character splitter,
        respecting specified chunk size and overlap settings or defaults.

        Args:
        text (str): The text content to be split into smaller chunks.
        chunk_size (int | None): Optional size limit for each chunk; if None, use default chunk_size attribute.
        chunk_overlap (int | None): Optional overlap size between consecutive chunks; if None, use default chunk_overlap attribute.

        Returns:
        List[str]: A list of text chunks split from the original text.
        """
        try:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size or self.chunk_size,
                chunk_overlap=chunk_overlap or self.chunk_overlap,
                separators=self.separators,
            )

            chunks = splitter.split_text(text)
            # example ["xxxxxxxxxxx", "zzzzzzzzzzz"]

            tracer.DEBUG(
                "split_text",
                "Text split into chunks",
                metadata={"chunks": len(chunks)}
            )

            return chunks
        except Exception as e:
            raise RuntimeError(f"Error splitting text into chunks: {str(e)}")

    @staticmethod
    def build_documents(chunks: List[str], metadata: Dict[str, Any]) -> List[Document]:
        """
        Creates Document objects from text chunks, attaching the given metadata to each document.

        chunks = ['Era uma vez uma cidade onde ninguém sonhava.\n\nNão porque fosse proibido, nem porque f... claro, ideias novas, perguntas perigosas.', 'Primeiro raros. Depois confusos. Depois intensos.\n\nE com eles vieram risos inesperado...que, de certa forma… nunca foi necessária.'],
        metadata = {'file_id': 'test_file_12345', 'created_at': '2026-04-30 19:49:35'}
        """
        try:
            return [
                Document(page_content=chunk, metadata={**metadata})
                for chunk in chunks
            ]
        except Exception as e:
            raise RuntimeError(f"Error building Document objects: {str(e)}")
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embeddings vectors for a list of texts using the embeddings model.

        Args:
        texts (List[str]): The list of text strings to embed.

        Returns:
        List[List[float]]: A list containing embedding vectors corresponding to each input text.
        """
        try:
            return self.embeddings_model.embed_documents(texts)
        except Exception as e:
            raise RuntimeError(f"Error generating embeddings: {str(e)}")


class PineconeEmbedding(EmbeddingHelpers):
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

            self.chunk_size = self.config.chunk_size
            self.chunk_overlap = self.config.chunk_overlap
            self.separators = self.config.separators
            self.namespace = self.config.namespace
            self.top_k = self.config.top_k
            self.delete_batch_size = self.config.delete_batch_size
            self.embedding_batch_size = self.config.embedding_batch_size

            self.embeddings_model = OpenAIEmbeddings(
                model=embedding_model_name or os.getenv(
                    "OPENAI_EMBEDDING_MODEL",
                    self.config.embedding_model
                )
            )

            self.dimensions = dimensions or self.config.dimensions

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
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap,
                    "separators": self.separators,

                    "top_k": self.top_k,
                    "delete_batch_size": self.delete_batch_size,
                    "embedding_batch_size": self.embedding_batch_size,

                    "embedding_model": embedding_model_name or os.getenv(
                        "OPENAI_EMBEDDING_MODEL",
                        self.config.embedding_model
                    ),

                    "dimensions": self.dimensions,
                    "main_namespace": self.client.main_namespace,
                    "global_namespace": self.client.global_namespace,
                    "index_name": getattr(self.client, "index_name", None),
                    "has_custom_client": vector_client is not None,
                }
            )

        except Exception as e:
            raise RuntimeError(f"Initialization failed - {str(e)}")


    def generate_vectors(
        self,
        text: str,
        metadata: dict,
        save_global: bool = False,
        batch_size: int | None = None,
    ):
        """
        Processes the input text by splitting it into chunks, creating Documents,
        generating embeddings, and saving these embeddings in Pinecone vector stores.
        Handles batching and optionally saves embeddings in a global namespace as well.

        Args:
        text (str): The full text content to generate vector embeddings from.
        metadata (dict): Dictionary metadata to associate with each vector embedding.
        save_global (bool): Whether to save embeddings also in the global namespace. Default is False.
        batch_size (int | None): Optional number of documents to embed per batch; defaults to internal config batch size.

        Returns:
        dict: A dictionary indicating success or error status, messages, and detailed embedding information.
        """
        dt_utc = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)
        metadata["created_at"] = str(dt_utc)

        chunks = self.split_text(text)
        documents = self.build_documents(chunks, metadata)

        """
        [Document(metadata={'file_id': 'test_file_12345', 'created_at': '2026-04-30 19:49:35'}...laro, ideias novas, perguntas perigosas.'),
        Document(metadata={'file_id': 'test_file_12345', 'created_at': '2026-04-30 19:49:35'}...e, de certa forma… nunca foi necessária.')],
        """

        batch_size = ( # 100
            min(batch_size, self.embedding_batch_size)
            if batch_size and batch_size > 0
            else self.embedding_batch_size
        )

        main_namespace_ids = []
        global_namespace_ids = []
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
                main_namespace_ids.extend(ids)

                if save_global:
                    ids = self.global_vectordb.add_documents(batch_docs)
                    global_namespace_ids.extend(ids)

        except Exception as error:
            tracer.ERROR(
                "generate_vectors",
                f"Batch failed, starting rollback - {str(error)}",
                metadata={"batch_number": batch_number}
            )

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
                "saved_ids": {
                    "main_namespace": main_namespace_ids,
                    "global_namespace": global_namespace_ids if save_global else []
                },
                "batch": batch_number
            }

        response = {
            "status": "success",
            "message": "Embeddings saved successfully.",
            "embedding_informations": {
                "batch_count": batch_number,
                "main_namespace": {
                    "namespace": self.client.main_namespace,
                    "chunks_saved": len(main_namespace_ids),
                    "chunks_ids": main_namespace_ids
                }
            }
        }

        if save_global:
            response["embedding_informations"]["global_namespace"] = {
                "namespace": self.client.global_namespace,
                "chunks_saved": len(global_namespace_ids),
                "chunks_ids": global_namespace_ids
            }

        tracer.DEBUG(
            "generate_vectors",
            "All batches processed",
            metadata={
                "total_batches": batch_number,
                "total_vectors": len(main_namespace_ids) + len(global_namespace_ids) if save_global else len(main_namespace_ids),
                "response": response,
            }
        )

        return response


    def delete_documents(
        self,
        target_feature: str,
        target_id: str,
        namespace: str,
        features: list = None
    ):
        """
        Deletes vectors from the Pinecone index matching a specific feature and id within a given namespace.
        Supports batch deletion for efficient processing and includes validation for the presence of the target feature.

        Args:
        target_feature (str): The metadata feature key to filter vectors for deletion.
        target_id (str): The specific feature value identifying which vectors to delete.
        namespace (str): The Pinecone namespace where deletion occurs.
        features (list): Optional list of valid feature keys; if provided, target_feature must be included.

        Returns:
        dict: Information about the number of deleted vectors and the namespace they were deleted from.

        Raises:
        ValueError: If target_feature is not found in the features list when features is provided.
        RuntimeError: If an error occurs during the deletion process.
        """
        if features and target_feature not in features:
            raise ValueError(f"Target feature '{target_feature}' not in provided features list")

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
            raise RuntimeError(f"Error deleting documents: {str(e)}")






if __name__ == "__main__":
    import json

    pine_client = PineconeClient(
        index_name="backai-vectorstore",
        main_namespace="embedding_file",
    )

    service = PineconeEmbedding(pine_client)
    response = service.generate_vectors(
        text="Teste de geração de embeddings com o Pinecone Vector Service",
        metadata={"file_id": "test_file_12345"},
        save_global=True
    )
    print(json.dumps(response, indent=4, default=str))

# python -m src.vector_store.pinecone.embedding
```