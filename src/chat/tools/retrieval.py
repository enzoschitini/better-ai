import os
import logging
from typing import List
from dotenv import load_dotenv

from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

import pinecone

# ========== LOGGING ==========
from src.chat.utils.logging_utils import setup_logging

setup_logging()

# ========== CONFIGURAÇÃO ==========
load_dotenv()
#logging.info("Variáveis de ambiente carregadas.")

# === CREDENCIAIS ===
openai_key = os.getenv("OPENAI_API_KEY")
pinecone_key = os.getenv("PINECONE_API_KEY")
index_name = os.getenv("PINECONE_INDEX_NAME")
namespace = os.getenv("PINECONE_NAMESPACE")

#logging.info(f"Pinecone Index configurado: {index_name}")
#logging.info(f"Namespace: {namespace}")

# === PINECONE INIT ===
pc = pinecone.Pinecone(api_key=pinecone_key)
index = pc.Index(index_name)

# === EMBEDDINGS ===
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")


class PineconeSimSearch:
    def __init__(self, index, embeddings, namespace=None):
        self.index = index
        self.embeddings = embeddings
        self.namespace = namespace
        #logging.info("PineconeSimSearch inicializado.")

    def similarity_search(self, query: str, k: int = 5, filter_search: dict = None) -> List[Document]:
        #logging.info("Iniciando similarity_search()")
        #logging.info(f"Query recebida: {query}")
        #logging.info(f"K={k}, Filtro={filter_search}")

        query_emb = self.embeddings.embed_query(query)
        #logging.info("Embedding gerado para a query.")

        # Aplica filtro se passado
        filter_query = None
        if filter_search:
            key, value = list(filter_search.items())[0]
            filter_query = {key: {"$eq": value}}
            #logging.info(f"Filtro formatado para Pinecone: {filter_query}")

        #logging.info("Realizando consulta ao Pinecone...")

        results = self.index.query(
            vector=query_emb,
            top_k=k,
            namespace=self.namespace,
            include_metadata=True,
            filter=filter_query
        )

        #logging.info(f"Retorno Pinecone: {len(results.get('matches', []))} documentos encontrados.")

        docs = []
        for match in results.get("matches", []):
            page_content = match.get("metadata", {}).get("text", "")
            docs.append(Document(page_content=page_content, metadata=match.get("metadata", {})))

        return docs


def VectorStorer():
    #logging.info("Instanciando VectorStore...")
    vectordb = PineconeSimSearch(index=index, embeddings=embeddings, namespace=namespace)
    return vectordb


def Similarity_Search(vectordb, query, k, filter_search):
    #logging.info("Rodando Similarity_Search()...")
    docs = vectordb.similarity_search(query, k=k, filter_search=filter_search)

    context = "\n\n".join([doc.page_content for doc in docs])
    #logging.info("Contexto concatenado com sucesso.")

    return {"docs": docs, "context": context}


def query_context(pergunta):
    #logging.info(f"Criando prompt de query_context() para pergunta: {pergunta}")

    prompt_template = PromptTemplate.from_template('''
Analise buscando por informações que possam responder a pergunta: {pergunta}                     
''')
    
    result = prompt_template.format(pergunta=pergunta)
    #logging.info("Prompt de busca gerado.")
    return result


def prompt(pergunta, context):
    #logging.info(f"Criando prompt final para LLM responder... Pergunta: {pergunta}")

    prompt_template = PromptTemplate.from_template('''
Analise o contexto para responder a seguinte pergunta: {pergunta}
                                                   
Contexto:
{context}
                                                   
Responda de forma clara e não invente informação.
''')
    
    result = prompt_template.format(pergunta=pergunta, context=context)
    #logging.info("Prompt final gerado.")
    return result


def AnswerGenerationTool(pergunta: str, AnswerGenerationDic: dict):
    #logging.info(f"=== Executando AnswerGenerationTool() ===")
    #logging.info(f"Pergunta: {pergunta}")
    #logging.info(f"Configurações recebidas: {AnswerGenerationDic}")

    vectordb = VectorStorer()
    llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0.5)
    #logging.info("LLM inicializado.")

    search_standards = Similarity_Search(
        vectordb=vectordb,
        query=query_context(pergunta),
        k=AnswerGenerationDic["K"],
        filter_search=AnswerGenerationDic["filter_search"]
    )

    context = search_standards["context"]
    #logging.info(f"Contexto retornado com {len(search_standards['docs'])} documentos.")

    return context

"""
retrieval = AnswerGenerationTool("Enzo Schitini", {"filter_search": {"collection_id": "22"}, "K": 50})
print(retrieval)
#"""