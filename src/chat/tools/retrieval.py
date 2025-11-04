from typing import List
import os
from dotenv import load_dotenv
import json
from pydantic import BaseModel, Field

from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser

import pinecone

# ========== CONFIGURAÇÃO ==========
load_dotenv()
#pp = p#print.Pretty#printer(indent=4)

# === CREDENCIAIS ===
openai_key = os.getenv("OPENAI_API_KEY")
pinecone_key = os.getenv("PINECONE_API_KEY")

# === PINECONE INIT ===
pc = pinecone.Pinecone(api_key=pinecone_key)
index_name = os.getenv("PINECONE_INDEX_NAME")
index = pc.Index(index_name)
namespace = os.getenv("PINECONE_NAMESPACE")

# === EMBEDDINGS ===
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

class PineconeSimSearch:
    def __init__(self, index, embeddings, namespace=None):
        self.index = index
        self.embeddings = embeddings
        self.namespace = namespace

    def similarity_search(self, query: str, k: int = 5, filter_search: dict = None) -> List[Document]:
        query_emb = self.embeddings.embed_query(query)
        
        # Aplica filtro se passado
        filter_query = None
        if filter_search:
            key, value = list(filter_search.items())[0]
            filter_query = {key: {"$eq": value}}
        
        results = self.index.query(
            vector=query_emb,
            top_k=k,
            namespace=self.namespace,
            include_metadata=True,
            filter=filter_query
        )

        docs = []
        for match in results.get("matches", []):
            page_content = match.get("metadata", {}).get("text", "")
            docs.append(Document(page_content=page_content, metadata=match.get("metadata", {})))
        return docs

def VectorStorer():
    # === Similarity search ===
    vectordb = PineconeSimSearch(index=index, embeddings=embeddings, namespace=namespace)

    return vectordb

def Similarity_Search(vectordb, query, k, filter_search):
    docs = vectordb.similarity_search(
        query,
        k=k,
        filter_search=filter_search
    )

    # === Concatenar textos dos documentos ===
    context = "\n\n".join([doc.page_content for doc in docs])

    return {"docs": docs, "context": context}

def query_context(pergunta):
    prompt_template = PromptTemplate.from_template('''
Analise buscando por informações que possam responder a pergunta: {pergunta}                     
''')
    
    return prompt_template.format(pergunta=pergunta)


def prompt(pergunta, context):
    prompt_template = PromptTemplate.from_template('''
Analise o contexto para responder a seguinte pergunta: {pergunta}
                                                   
Contexto:
{context}
                                                   
Responda de forma clara e não invente informação.
''')
    
    return prompt_template.format(pergunta=pergunta, context=context)


def AnswerGenerationTool(pergunta: str, AnswerGenerationDic: dict):
    # === Inicializa VectorStore ===
    vectordb = VectorStorer()

    # === Inicializa LLM ===
    llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0.5)

    # === Busca nos standards ===
    search_standards = Similarity_Search(
        vectordb=vectordb, 
        query=query_context(pergunta), 
        k=5, 
        filter_search=AnswerGenerationDic["filter_search"]
    )

    context = search_standards["context"]

    # === Obter resposta da Chain ===
    #input_prompt = prompt(pergunta, context)
    #response = llm.invoke(input_prompt)

    # === Retorna a resposta em texto ===
    #string_response = response.content
    return context

