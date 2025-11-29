import json
from bson import ObjectId
import logging
from src.chat.utils.logging_utils import setup_logging

setup_logging()

class BusinessRepository:
    """Abstrai o acesso ao MongoDB e ao arquivo local JSON."""

    def __init__(self, mongo, json_path: str = "src/chat/tokens_calculator/business_acess.json"):
        self.mongo = mongo
        self.json_path = json_path
        logging.info(f"BusinessRepository inicializado com JSON em: {self.json_path}")

    def get_business_data(self, business_id: str) -> dict:
        logging.info(f"Buscando dados para business_id={business_id} no MongoDB.")

        try:
            docs = self.mongo.buscar_documentos(
                "TokensUsage",
                "BusinessAccountManage",
                {"business_id": business_id}
            )

            if docs:
                logging.info(f"Documento encontrado para business_id={business_id}")
                return docs[0]
            else:
                logging.warning(f"Nenhum documento encontrado para business_id={business_id}")
                return None
        except Exception as e:
            logging.exception(f"Erro ao buscar dados no MongoDB para business_id={business_id}")
            raise

    def update_business_data(self, mongo_id: str, new_data: dict):
        logging.info(f"Iniciando atualização do documento MongoDB _id={mongo_id}")

        try:
            filtro = {'_id': ObjectId(mongo_id)}
            self.mongo.atualizar_documentos(
                "TokensUsage",
                "BusinessAccountManage",
                filtro,
                new_data
            )
            logging.info(f"Documento _id={mongo_id} atualizado com sucesso.")
        except Exception as e:
            logging.exception(f"Erro ao atualizar documento _id={mongo_id}")
            raise

    def insert_process_tokens_usage(self, tokens_response):
        logging.info("Inserindo registro de uso de tokens em ChatTokensUsage.")

        try:
            self.mongo.salvar_payload(
                "TokensUsage",
                "ChatTokensUsage",
                tokens_response
            )
            logging.info("Registro inserido com sucesso em ChatTokensUsage.")
        except Exception:
            logging.exception("Erro ao inserir registro em ChatTokensUsage.")
            raise

    def update_local_status(self, business_id: str, new_status: str):
        logging.info(f"Atualizando status local para business_id={business_id}, novo status={new_status}")

        try:
            logging.info(f"Lendo arquivo local: {self.json_path}")
            with open(self.json_path, "r", encoding="utf-8") as f:
                dados = json.load(f)

            encontrado = False

            for item in dados:
                if item.get("business_id") == business_id:
                    item["status_plan"] = new_status
                    encontrado = True
                    logging.info(f"Status atualizado no JSON para business_id={business_id}")
                    break

            if not encontrado:
                logging.warning(f"Business_id={business_id} não encontrado no JSON.")

            logging.info(f"Salvando alterações no arquivo {self.json_path}")
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(dados, f, indent=4, ensure_ascii=False)

            logging.info("Arquivo JSON salvo com sucesso.")

        except FileNotFoundError:
            logging.exception(f"Arquivo {self.json_path} não encontrado.")
            raise
        except json.JSONDecodeError:
            logging.exception(f"Erro ao decodificar JSON em {self.json_path}.")
            raise
        except Exception:
            logging.exception(f"Erro inesperado ao atualizar status local para business_id={business_id}")
            raise
