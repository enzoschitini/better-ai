import os
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
