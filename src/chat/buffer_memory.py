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

import logging
from src.chat.utils.logging_utils import setup_logging

setup_logging()

load_dotenv()


# =========================================
# CONFIGURAÇÃO DO MONGO
# =========================================
#logging.info("Carregando configuração do MongoDB...")

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    logging.error("Variável de ambiente MONGO_URI não configurada.")
    raise EnvironmentError("⚠️ Variável de ambiente MONGO_URI não configurada.")

try:
    client = MongoClient(MONGO_URI)
    db = client["Chat"]
    collection = db["ConversationBufferMemory"]
    #logging.info("Conexão com MongoDB realizada com sucesso.")
except Exception as e:
    logging.exception(f"Erro ao conectar ao MongoDB: {e}")
    raise


# =========================================
# FUNÇÕES DE PERSISTÊNCIA
# =========================================
def save_chat_history(session_id: str, memory: ConversationBufferMemory) -> None:
    """
    Salva o histórico de chat de uma sessão no MongoDB.
    """
    #logging.info(f"Iniciando save_chat_history() | session_id={session_id}")

    if not session_id or not memory:
        logging.error("save_chat_history chamado sem session_id ou memory válidos.")
        raise ValueError("session_id e memory são obrigatórios para salvar o histórico.")

    try:
        history_data = messages_to_dict(memory.chat_memory.messages)
        collection.update_one(
            {"session_id": session_id},
            {"$set": {"messages": history_data}},
            upsert=True
        )
        #logging.info(f"Histórico salvo com sucesso para session_id={session_id}")
    except Exception as e:
        logging.exception(f"Erro ao salvar histórico da sessão {session_id}: {e}")
        raise


def load_chat_history(session_id: str):
    """
    Carrega o histórico de chat de uma sessão no MongoDB.
    Retorna uma lista de mensagens.
    """
    #logging.info(f"Iniciando load_chat_history() | session_id={session_id}")

    if not session_id:
        logging.warning("load_chat_history chamado sem session_id. Retornando vazio.")
        return []

    try:
        doc = collection.find_one({"session_id": session_id})
        if doc and "messages" in doc:
            #logging.info(f"Histórico encontrado para session_id={session_id}.")
            return messages_from_dict(doc["messages"])

        #logging.info(f"Nenhum histórico encontrado para session_id={session_id}.")
        return []

    except Exception as e:
        logging.exception(f"Erro ao carregar histórico da sessão {session_id}: {e}")
        raise


def create_memory(session_id: str) -> ConversationBufferMemory:
    """
    Cria uma instância de memória persistente associada a uma sessão específica.
    Retorna um objeto ConversationBufferMemory com as mensagens carregadas.
    """
    #logging.info(f"Inicializando memória para session_id={session_id}")

    try:
        loaded_messages = load_chat_history(session_id)

        memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history"
        )
        memory.chat_memory.messages = loaded_messages

        logging.debug(
            f"Memória criada para session_id={session_id} | mensagens_carregadas={len(loaded_messages)}"
        )
        return memory

    except Exception as e:
        logging.exception(f"Erro ao criar memória para session_id={session_id}: {e}")
        raise


# =========================================
# TESTE LOCAL (opcional)
# =========================================
if __name__ == "__main__":
    try:
        sess_id = "teste_123"
        logging.info(f"=== Teste local iniciado para session_id={sess_id} ===")

        mem = create_memory(sess_id)

        from langchain.schema import HumanMessage
        mem.chat_memory.add_message(HumanMessage(content="Olá!"))

        save_chat_history(sess_id, mem)

        mem2 = create_memory(sess_id)

        logging.info(
            f"Teste finalizado | Mensagens carregadas: {len(mem2.chat_memory.messages)}"
        )

    except Exception as e:
        logging.exception(f"Erro no teste local: {e}")
