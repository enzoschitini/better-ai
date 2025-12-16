import os
from dotenv import load_dotenv
from datetime import datetime, timezone

from pinecone import Pinecone

from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

load_dotenv()

class PineconeClient:
    """
    Responsável apenas por criar conexão com o Pinecone e manter o Index.
    """
    def __init__(self, index_name: str = None, namespace: str = None, global_namespace: str = None):
        self.index_name = index_name or os.getenv("INDEX_NAME_PINECONE")
        self.main_namespace = namespace or os.getenv("KNOWLEDGE_BASE_PINECONE")
        self.global_namespace = global_namespace or os.getenv("PINECONE_GLOBAL_NAMESPACE")

        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index = self.pc.Index(self.index_name)

    def create_vector_store(self, embeddings_model, namespace) -> PineconeVectorStore:
        """Factory method: cada VectorStore é criado com um namespace específico."""
        return PineconeVectorStore(
            index=self.index,
            embedding=embeddings_model,
            text_key="text",
            namespace=namespace
        )


class PineconeVectorService:
    """
    Service responsável por:
    - transformar texto em chunks
    - gerar embeddings
    - salvar nos dois namespaces
    """
    def __init__(self, vector_client: PineconeClient, embedding_model_name: str = None, dimensions: int = None):
        self.client = vector_client

        self.embeddings_model = OpenAIEmbeddings(
            model=embedding_model_name or os.getenv("KNOWLEDGE_BASE_EMBEDDINGS_MODEL", "text-embedding-3-small")
        )

        self.dimensions = dimensions or 1536

        # Vector store para o namespace global
        self.global_vectordb = self.client.create_vector_store(
            embeddings_model=self.embeddings_model,
            namespace=self.client.global_namespace
        )

        # Vector store para o namespace principal (base de conhecimento)
        self.main_vectordb = self.client.create_vector_store(
            embeddings_model=self.embeddings_model,
            namespace=self.client.main_namespace
        )

    # ----------------- Helpers ------------------

    @staticmethod
    def split_text(text: str, chunk_size: int = 3000, chunk_overlap: int = 300):
        """Divide texto em chunks."""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", " "]
        )
        return splitter.split_text(text)

    @staticmethod
    def build_documents(chunks: list[str], metadata: dict):
        """Cria objetos Document a partir dos chunks."""
        return [Document(page_content=chunk, metadata={**metadata}) for chunk in chunks]

    def delete_documents(self, target_feature: str, target_id: str, namespace: str):
        """Remove embeddings de um namespace específico."""
        results = self.client.index.query(
            vector=[0.0] * self.dimensions,
            namespace=namespace,
            filter={target_feature: {"$eq": target_id}},
            top_k=10000,
        )

        ids_to_delete = [match["id"] for match in results.get("matches", [])]

        if ids_to_delete:
            batch_size = 1000
            for i in range(0, len(ids_to_delete), batch_size):
                batch = ids_to_delete[i:i + batch_size]
                self.client.index.delete(ids=batch, namespace=namespace)

            return f"✅ {len(ids_to_delete)} vetores apagados de `{namespace}`"

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

    def generate_vectors(self, text: str, metadata: dict, save_global: bool = False, batch_size: int = 100):
        """
        Salva embeddings no namespace principal (KB).
        Se save_global=True, também salva no namespace global.
        """

        dt_utc = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)
        metadata["creat_date_utc"] = str(dt_utc)
        
        chunks = self.split_text(text)
        documents = self.build_documents(chunks, metadata)

        # Trava de segurança
        if batch_size > 100:
            batch_size = 100

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
                print("Enviando batch_docs para o Pinecone...")
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
                "chunks_ids": all_ids,
                "batch_count": batch_number
            }
        }

        return response








"""
# python -m src.embedding.pinecone_vector_store

pine_client = PineconeClient(index_name="backai-vectorstore", namespace="test_namespace", global_namespace="global_namespace")
pine_service = PineconeVectorService(pine_client, embedding_model_name="text-embedding-3-large", dimensions=3072)

embedding_content = 
Sono uno sviluppatore con 4 anni di esperienza in progetti che combinano prestazioni, 
scalabilità e best practice.

Sono un esperto di Intelligenza Artificiale, Machine Learning e dati, con una solida 
esperienza nello sviluppo di applicazioni complete e scalabili. 

Negli ultimi anni ho lavorato su diversi progetti in diversi settori, tra cui intelligenza artificiale, 
ho seguito da vicino l’evoluzione dell’AI Generativa, partendo dai primi esperimenti con gli AI 
Agents fino allo sviluppo di sistemi complessi di orchestrazione e automazione. Progettando 
architetture RAG, orchestrando modelli LLM e integrato strumenti come LangChain, 
LlamaIndex, Crewai e Dify per creare agenti intelligenti in grado di ragionare, pianificare e 
interagire in modo autonomo. 

La mia conoscenza dei modelli di Machine Learning deriva dalla mia esperienza come Data 
Scientist e Data Analyst, dove unisco l’approccio analitico alla capacità di tradurre i dati in 
strategie concrete. Laureato all'EBAC, con competenze in statistica, modelli di 
apprendimento automatico, Python, SQL, creazione di dashboard con Streamlit, GitHub, 
Excel, tra gli altri. Sempre alla ricerca di insight nascosti, quei dettagli non sempre evidenti 
ma di immenso valore per il business. 

Ho lavorato anche come sviluppatore Bubble, realizzando siti web, landing page e 
applicazioni complete senza codice, ma con logiche avanzate e un approccio da vero 
sviluppatore software. Nel tempo ho creato piattaforme SaaS, sistemi gestionali, 
marketplace e app educative, integrando API esterne, database complessi e automazioni 
intelligenti. 

Da quando avevo 12 anni, quando ho iniziato a studiare robotica, ho coltivato la mia 
passione per lo sviluppo software. Credo nell'apprendimento pratico e so che, con dedizione, 
impegno e pazienza, è possibile ottenere grandi risultati.  
Oggi rimango motivato a sfidare la mia creatività e cercare nuovi modi per innovare e avere 
un impatto positivo sul mondo che mi circonda.


embedding_metadata = {"user_id": "user_123", "source": "embedding_test.py"}

response = pine_service.generate_vectors(
    text=str(embedding_content),
    metadata=embedding_metadata,
    save_global=False,
    batch_size=200
)

print("✅ Vectors generated and saved to Pinecone:", response)
"""