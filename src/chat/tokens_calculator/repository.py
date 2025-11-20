import json
from bson import ObjectId
import logging

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(filename)s - line: %(lineno)d - %(levelname)s - %(message)s'
)

class BusinessRepository:
    """Abstrai o acesso ao MongoDB e ao arquivo local JSON."""

    def __init__(self, mongo, json_path: str = "src/chat/tokens_calculator/business_acess.json"):
        self.mongo = mongo
        self.json_path = json_path

    def get_business_data(self, business_id: str) -> dict:
        docs = self.mongo.buscar_documentos(
            "TokensUsage",
            "BusinessAccountManage",
            {"business_id": business_id}
        )
        return docs[0] if docs else None

    def update_business_data(self, mongo_id: str, new_data: dict):
        filtro = {'_id': ObjectId(mongo_id)}
        self.mongo.atualizar_documentos(
            "TokensUsage",
            "BusinessAccountManage",
            filtro,
            new_data
        )
    
    def insert_process_tokens_usage(self, tokens_response):
        self.mongo.salvar_payload(
            "TokensUsage",
            "ProcessTokensUsage",
            tokens_response
        )

    def update_local_status(self, business_id: str, new_status: str):
        with open(self.json_path, "r", encoding="utf-8") as f:
            dados = json.load(f)

        for item in dados:
            if item.get("business_id") == business_id:
                item["status_plan"] = new_status

        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)
