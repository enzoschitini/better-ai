import sys
from pathlib import Path

# Adiciona a pasta "src" ao sys.path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.chat.utils.mongo_manage import MongoDBManager
from src.chat.tokens_calculator.manager import BusinessPlanManager

def menage_chat_usage(BUSINESS_ID, MODEL, tokens_response):
    try:
        mongo = MongoDBManager()
        manager = BusinessPlanManager(BUSINESS_ID, MODEL, tokens_response, mongo)
        resultado = manager.execute()
    except Exception as e:
        return {
            "message": f"Erro ao gerenciar o uso do chat",
            "status": "error"
        }

