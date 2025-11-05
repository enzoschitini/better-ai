# MongoDB.py
"""
Módulo responsável pela persistência de memória de chat no MongoDB.
Refatorado segundo SOLID — Single Responsibility e Dependency Inversion.
"""

import os
from pymongo import MongoClient
from langchain.memory import ConversationBufferMemory
from langchain.schema import messages_from_dict, messages_to_dict
from dotenv import load_dotenv

load_dotenv()


# =========================================
# CONFIGURAÇÃO DO MONGO
# =========================================
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise EnvironmentError("⚠️ bm bm Variável de ambiente MONGO_URI não configurada.")

client = MongoClient(MONGO_URI)
db = client["Chat"]
collection = db["ConversationBufferMemory"]


# =========================================
# FUNÇÕES DE PERSISTÊNCIA
# =========================================
def save_chat_history(session_id: str, memory: ConversationBufferMemory) -> None:
    """
    Salva o histórico de chat de uma sessão no MongoDB.
    """
    if not session_id or not memory:
        raise ValueError("session_id e memory são obrigatórios para salvar o histórico.")

    history_data = messages_to_dict(memory.chat_memory.messages)
    collection.update_one(
        {"session_id": session_id},
        {"$set": {"messages": history_data}},
        upsert=True
    )


def load_chat_history(session_id: str):
    """
    Carrega o histórico de chat de uma sessão no MongoDB.
    Retorna uma lista de mensagens.
    """
    if not session_id:
        return []

    doc = collection.find_one({"session_id": session_id})
    if doc and "messages" in doc:
        return messages_from_dict(doc["messages"])
    return []


def create_memory(session_id: str) -> ConversationBufferMemory:
    """
    Cria uma instância de memória persistente associada a uma sessão específica.
    Retorna um objeto ConversationBufferMemory com as mensagens carregadas.
    """
    loaded_messages = load_chat_history(session_id)

    memory = ConversationBufferMemory(
        return_messages=True,
        memory_key="chat_history"
    )
    memory.chat_memory.messages = loaded_messages
    return memory


# =========================================
# TESTE LOCAL (opcional)
# =========================================
if __name__ == "__main__":
    # Teste rápido
    sess_id = "teste_123"
    mem = create_memory(sess_id)

    #print(f"Mensagens carregadas ({sess_id}):", len(mem.chat_memory.messages))

    # simulação de adição
    from langchain.schema import HumanMessage
    mem.chat_memory.add_message(HumanMessage(content="Olá!"))
    save_chat_history(sess_id, mem)

    mem2 = create_memory(sess_id)
    #print(f"Mensagens recarregadas: {len(mem2.chat_memory.messages)}")
