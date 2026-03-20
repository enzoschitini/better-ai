import os
from dotenv import load_dotenv
from datetime import datetime, timezone

from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from src.vector_store.pinecone.pinecone_client import PineconeClient
from src.vector_store.config import PineconeVectorStoreConfig
load_dotenv()


class PineconeVectorService:
    """
    Service responsável por:
    - transformar texto em chunks
    - gerar embeddings
    - salvar nos dois namespaces
    """
    def __init__(self, vector_client = PineconeClient(), embedding_model_name: str = None, dimensions: int = None):
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
            model=embedding_model_name or os.getenv("OPENAI_EMBEDDING_MODEL", self.config.embedding_model)
        )

        self.dimensions = dimensions or self.config.dimensions

        # Vector store para o namespace global
        self.global_vectordb = self.client.create_vector_store(
            embedding_model=self.embeddings_model,
            namespace=self.client.global_namespace
        )

        # Vector store para o namespace principal (base de conhecimento)
        self.main_vectordb = self.client.create_vector_store(
            embedding_model=self.embeddings_model,
            namespace=self.client.main_namespace
        )

    # ----------------- Helpers ------------------
    def split_text(
        self,
        text: str,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ):
        """Divide texto em chunks."""
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size if chunk_size is not None else self.chunk_size,
            chunk_overlap=chunk_overlap if chunk_overlap is not None else self.chunk_overlap,
            separators=self.separators,
        )
        
        return splitter.split_text(text)

    @staticmethod
    def build_documents(chunks: list[str], metadata: dict):
        """Cria objetos Document a partir dos chunks."""
        return [Document(page_content=chunk, metadata={**metadata}) for chunk in chunks]

    def delete_documents(self, target_feature: str, target_id: str, namespace: str):
        """Remove embeddings de um namespace específico."""
        namespace = namespace if namespace is not None else self.namespace
        results = self.client.index.query(
            vector=[0.0] * self.dimensions,
            namespace=namespace,
            filter={target_feature: {"$eq": target_id}},
            top_k=self.top_k,
        )

        ids_to_delete = [match["id"] for match in results.get("matches", [])]

        if ids_to_delete:
            batch_size = self.delete_batch_size
            for i in range(0, len(ids_to_delete), batch_size):
                batch = ids_to_delete[i:i + batch_size]
                self.client.index.delete(ids=batch, namespace=namespace)

            return {
                "deleted_vectors": len(ids_to_delete),
                "message": f"✅ {len(ids_to_delete)} vetores apagados de `{namespace}`"
            }

        return f"Nenhum vetor encontrado em `{namespace}`"
    
    # ----------------- Similarity Search ------------------

    def document_search(self, query: str, k: int = 3, namespace: str = None, filter: dict = None):
        """
        Busca documentos no Pinecone usando similarity_search.

        Args:
            query (str): Texto a ser buscado.
            k (int): Quantidade de resultados.
            namespace (str): Namespace onde será feita a consulta.
                             Se None, usa o namespace principal (embeddings da KB).
            filter (dict): Filtro opcional, exemplo:
                           {"file_id": {"$eq": "<id_do_arquivo>"}}

        Returns:
            list[Document]: documentos encontrados com page_content + metadata
        """

        # Usa o namespace adequado (KB ou global)
        selected_namespace = namespace or self.client.main_namespace

        # Cria um vectorstore específico para busca (com filtro opcional)
        vectordb = self.client.create_vector_store(
            embeddings_model=self.embeddings_model,
            namespace=selected_namespace
        )

        # Realiza a busca por similaridade usando embeddings
        search_results = vectordb.similarity_search(
            query=query,
            k=k,
            filter=filter  # <-- filtro aplicado
        )

        results = {}

        for result in search_results:
            insert = {
                "metadata": result.metadata,
                "page_content": result.page_content
            }
            
            results[result.id] = insert

        return results


    # ----------------- Embeddings ------------------

    def generate_vectors(
        self,
        text: str,
        metadata: dict,
        save_global: bool = False,
        batch_size: int | None = None,
    ):
        """
        Salva embeddings no namespace principal (KB).
        Se save_global=True, também salva no namespace global.
        """

        dt_utc = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)
        metadata["created_at"] = str(dt_utc)
        
        chunks = self.split_text(text)
        documents = self.build_documents(chunks, metadata)

        # Trava de segurança para batch_size
        if batch_size is None or batch_size <= 0:
            batch_size = self.embedding_batch_size
        else:
            batch_size = min(batch_size, self.embedding_batch_size)

        all_ids = []
        batch_number = 0

        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i : i + batch_size]
            batch_number += 1

            """
            # Test
            for doc in batch_docs:
                print(f"len: {len(doc.page_content)}") 
                print(f"chunk: {doc.page_content[:80]}...")
            """

            try:
                print("Sending batch_docs to Pinecone...")
                #if batch_number == 3:
                    #raise Exception("Erro forçado após 3 execuções do loop")

                # Sempre salva no namespace principal
                ids = self.main_vectordb.add_documents(batch_docs)
                all_ids.extend(ids)

                # Opcional: salva também no namespace global
                if save_global:
                    self.global_vectordb.add_documents(batch_docs)

            except Exception as error:
                self.delete_documents("file_id", metadata.get("file_id"), self.client.main_namespace)
                self.delete_documents("file_id", metadata.get("file_id"), self.client.global_namespace)
                
                """
                print(f"Erro no batch {batch_number}: {error}")
                #print(self.delete_documents("file_id", metadata.get("file_id"), self.client.main_namespace))

                if save_global:
                    print(self.delete_documents("file_id", metadata.get("file_id"), self.client.global_namespace))
                """

                response = {
                    "status": "error",
                    "message": "Erro ao salvar embeddings no Pinecone.",
                    "error": str(error),
                    "saved_ids": all_ids,
                    "namespace_main": self.client.main_namespace,
                    "namespace_global": self.client.global_namespace if save_global else None,
                    "batch": batch_number
                }

                return response

        response = {
            "status": "success",
            "message": "Embeddings salvos com sucesso no Pinecone.",
            "embedding_informations": {
                "namespace_main": self.client.main_namespace,
                "namespace_global": self.client.global_namespace if save_global else None,
                "batch_count": batch_number,
                "chunks_ids": all_ids
            }
        }

        return response




def embedding_test():
    pine_service = PineconeVectorService(embedding_model_name="text-embedding-3-large", dimensions=3072)

    embedding_content = """
Embeddings are vector representations of data (such as text, documents, or images) that capture their semantic meaning in a numerical space.
This technique allows for the comparison of content by similarity, enabling semantic searches, classification, recommendation, and information retrieval.
By transforming unstructured data into vectors, embeddings make it possible to efficiently index and query large volumes of information in vector databases.
"""

    embedding_metadata = {"user_id": "user_1234567", "source": "embedding_test.py"}

    response = pine_service.generate_vectors(
        text=str(embedding_content),
        metadata=embedding_metadata,
        save_global=False,
        batch_size=200
    )

    print("✅ Vectors generated and saved to Pinecone:", response)

def delete_test():
    #pine_client = PineconeClient(index_name="backai-vectorstore", namespace="test_namespace", global_namespace="global_namespace")
    pine_service = PineconeVectorService(embedding_model_name="text-embedding-3-large", dimensions=3072)

    delete = pine_service.delete_documents("source", "embedding_test.py", "betterai-embeddings-dev1")
    print(f"\n{delete}\n")

    return delete

#print(embedding_test())
#print(delete_test())

# python -m src.vector_store.pinecone.pinecone_vectorstore_services