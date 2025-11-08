import os
import uuid
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

load_dotenv()


class PineconeCRUD:
    def __init__(
        self,
        index_name: str = "backai-vectorstore",
        namespace: str = "default_namespace"
    ):
        # 🔹 Conectar ao Pinecone
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index = self.pc.Index(index_name)

        # 🔹 Guardar namespace
        self.namespace = namespace

        # 🔹 Modelo de embeddings
        self.embeddings_model = OpenAIEmbeddings(model="text-embedding-3-large")

        # 🔹 Vectorstore LangChain com namespace
        self.vectordb = PineconeVectorStore(
            index=self.index,
            embedding=self.embeddings_model,
            text_key="text",
            namespace=self.namespace
        )

        # 🔹 Splitter otimizado — mais contexto por chunk
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=3500,
            chunk_overlap=300,
            separators=["\n\n", "\n", ".", " "]
        )

    # ======================
    # CREATE
    # ======================
    def create_from_text(self, raw_text: str, metadata: dict = None):
        """Divide texto longo em chunks e envia ao Pinecone"""
        chunks = self.text_splitter.split_text(raw_text)

        documents = [
            Document(
                page_content=chunk,
                metadata={**(metadata or {})}
            )
            for chunk in chunks
        ]

        ids = self.vectordb.add_documents(documents)
        print(f"✅ Inseridos {len(ids)} chunks no namespace '{self.namespace}'.")
        return ids

    # ======================
    # READ (corrigido)
    # ======================
    def read_documents(self, filtro: dict = None, ids: list = None, k: int = 100):
        """Lê documentos via filtro ou IDs"""
        if ids:
            print(f"📥 Buscando {len(ids)} IDs no namespace '{self.namespace}'...")
            data = self.index.fetch(ids=ids, namespace=self.namespace)
            return data

        elif filtro:
            print(f"🔍 Buscando documentos com filtro {filtro}...")

            # Gera embedding neutro (evita query vazia)
            query_emb = self.embeddings_model.embed_query("texto neutro")

            resp = self.index.query(
                vector=query_emb,
                top_k=k,
                include_metadata=True,
                namespace=self.namespace,
                filter=filtro
            )

            docs = []
            for match in resp.get("matches", []):
                meta = match.get("metadata", {})
                docs.append(
                    Document(
                        page_content=meta.get("text", ""),
                        metadata=meta
                    )
                )

            print(f"📄 {len(docs)} documentos encontrados com o filtro.")
            return docs

        else:
            raise ValueError("❌ É necessário fornecer 'ids' ou 'filtro' para ler documentos.")


embedding_text = """
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
"""

metadata_dict = {
    "message": "File uploaded successfully!",
    "metadata": {
        "embedding_filter": {
            "file_ids": "1234",
            "collection_id": "22",
            "file_id": "49a03cc1-8119-47dd-b98c-5397ab648e35"
        },
        "embedding_aggregations": {
            "collection_name": "Babbel",
            "file_name": "Candidatura",
            "file_extension": "pdf"
        }
    }
}

"""
crud = PineconeCRUD(namespace="CRUD")

crud.create_from_text(
    raw_text=embedding_text,
    metadata=metadata_dict["metadata"]["embedding_filter"]
)
"""