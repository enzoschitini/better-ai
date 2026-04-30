import os
import logging

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
logging.getLogger("httpx").setLevel(logging.WARNING)

tracer = ApplicationTracing(
    flag="PineconeVectorService",
    file_name="pinecone_vector_service.py",
    log_file_name="pinecone_module"
)


class PineconeVectorService:
    """
    Service responsável por:
    - transformar texto em chunks
    - gerar embeddings
    - salvar nos namespaces
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
            tracer.ERROR("__init__", f"Initialization failed - {str(e)}")
            raise












    # ======================================================
    # Helpers
    # ======================================================
    def split_text(
        self,
        text: str,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> List[str]:

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

    @staticmethod
    def build_documents(chunks: List[str], metadata: Dict[str, Any]) -> List[Document]:
        """
        chunks = ['Era uma vez uma cidade onde ninguém sonhava.\n\nNão porque fosse proibido, nem porque f... claro, ideias novas, perguntas perigosas.', 'Primeiro raros. Depois confusos. Depois intensos.\n\nE com eles vieram risos inesperado...que, de certa forma… nunca foi necessária.'],
        metadata = {'file_id': 'test_file_12345', 'created_at': '2026-04-30 19:49:35'}
        """
        return [
            Document(page_content=chunk, metadata={**metadata})
            for chunk in chunks
        ]









    def delete_documents(
        self,
        target_feature: str,
        target_id: str,
        namespace: str
    ):

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
                f"Deletion failed - {str(e)}",
                metadata={
                    "target_feature": target_feature,
                    "target_id": target_id,
                }
            )
            raise







    # ======================================================
    # Embeddings
    # ======================================================
    def generate_vectors(
        self,
        text: str,
        metadata: dict,
        save_global: bool = False,
        batch_size: int | None = None,
    ):

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

        all_ids = []
        batch_number = 0

        try:
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i: i + batch_size]
                batch_number += 1

                texts = [doc.page_content for doc in batch_docs]
                metadatas = [doc.metadata for doc in batch_docs]

                embeddings = self.embeddings_model.embed_documents(texts)         
                # [[0.0006260871887207031, -0.01071929931640625, -0.0006003379821777344, 0.01102447509765625, -0.03997802734375, -0.00811767578125, 0.00514984130859375, 0.028533935546875, -0.027587890625, 0.0021533966064453125, 0.0136871337890625, 0.05810546875, -0.03985595703125, 0.01318359375, 0.0206298828125, 0.0272064208984375, 0.00434112548828125, 0.01045989990234375, -0.0028591156005859375, ...], [0.030303955078125, 0.004589080810546875, -0.0083160400390625, 0.0243377685546875, -0.0289764404296875, 0.0159454345703125, -0.03228759765625, 0.02490234375, -0.043670654296875, -0.02734375, 0.0219573974609375, 0.053070068359375, -0.038604736328125, 0.0155487060546875, -0.004741668701171875, -0.02117919921875, 0.0191192626953125, 0.0126953125, -0.0227813720703125, ...]]       

                """
                texts = [doc.page_content for doc in batch_docs]
                metadatas = [doc.metadata for doc in batch_docs]

                # 🔥 1. gerar embeddings (AGORA você tem acesso)
                embeddings = self.embeddings_model.embed_documents(texts)

                # 🔥 2. (opcional) salvar localmente
                for text, emb in zip(texts, embeddings):
                    print("TEXT:", text[:50])
                    print("EMB SIZE:", len(emb))

                # 🔥 3. enviar pro Pinecone manualmente
                vectors = [
                    {
                        "id": f"{metadata.get('file_id')}_{batch_number}_{i}",
                        "values": emb,
                        "metadata": metadata
                    }
                    for i, (emb, metadata) in enumerate(zip(embeddings, metadatas))
                ]

                self.client.index.upsert(
                    vectors=vectors,
                    namespace=self.client.main_namespace
                )

                ids = [v["id"] for v in vectors]
                all_ids.extend(ids)

                # 🔥 4. global (se quiser)
                if save_global:
                    self.client.index.upsert(
                        vectors=vectors,
                        namespace=self.client.global_namespace
                    )
                """

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
                f"Batch failed, starting rollback - {str(error)}",
                metadata={"batch_number": batch_number}
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

        """
        response = {'status': 'success', 'message': 'Embeddings saved successfully.', 'embedding_informations': {'namespace_main': 'embedding_file', 'namespace_global': 'embed_module', 'batch_count': 1, 'chunks_ids': [...]}}
        """
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



if __name__ == "__main__":
    import json

    pine_client = PineconeClient(
        index_name="backai-vectorstore",
        main_namespace="embedding_file",
    )

    service = PineconeVectorService(pine_client)
    response = service.generate_vectors(
        text="Teste de geração de embeddings com o Pinecone Vector Service",
        metadata={"file_id": "test_file_12345"},
        save_global=True
    )
    print(json.dumps(response, indent=4, default=str))

# python -m src.vector_store.pinecone.pinecone_vectorstore_services