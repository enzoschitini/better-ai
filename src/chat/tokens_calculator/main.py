import sys
from pathlib import Path
import logging

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(filename)s - line: %(lineno)d - %(levelname)s - %(message)s'
)

# Adiciona a pasta "src" ao sys.path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.chat.utils.mongo_manage import MongoDBManager
from src.chat.tokens_calculator.manager import BusinessPlanManager


def menage_chat_usage(BUSINESS_ID, MODEL, tokens_response):
    logging.info(
        f"[menage_chat_usage] Iniciando controle de uso — BUSINESS_ID={BUSINESS_ID}, MODEL={MODEL}"
    )

    try:
        # Log da entrada dos tokens
        logging.debug(
            f"[menage_chat_usage] Tokens recebidos: {tokens_response}"
        )

        mongo = MongoDBManager()
        logging.info("[menage_chat_usage] MongoDBManager instanciado com sucesso.")

        manager = BusinessPlanManager(BUSINESS_ID, MODEL, tokens_response, mongo)
        logging.info(
            f"[menage_chat_usage] BusinessPlanManager criado — empresa={BUSINESS_ID}, modelo={MODEL}"
        )

        resultado = manager.execute()
        logging.info(
            f"[menage_chat_usage] Gerenciamento de uso concluído com sucesso — resultado={resultado}"
        )

        return {
            "message": "Uso gerenciado com sucesso",
            "status": "success",
            "data": resultado
        }

    except Exception as e:
        logging.error(
            f"[menage_chat_usage] ERRO ao gerenciar uso — empresa={BUSINESS_ID}, modelo={MODEL}, erro={str(e)}"
        )

        return {
            "message": "Erro ao gerenciar o uso do chat",
            "status": "error",
            "error": str(e)
        }
