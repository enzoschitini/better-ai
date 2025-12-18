import os
from dotenv import load_dotenv
from io import BytesIO
from decimal import Decimal

import json
from copy import deepcopy

from src.chat.utils.mongo_manage import MongoDBManager
from src.embedding.file_content_extractor import FileContentExtractor
from src.embedding.pinecone_vector_store import PineconeClient, PineconeVectorService
from src.embedding.tokens_calculator.cost import EmbeddingCostCalculator

load_dotenv()



payload = {
    "company_id": "1",
    "file_id": "21d75dca2eec7b02080327f40220e20dxx2.pdf",
    "fileName": "name file.pdf",
    "fileUrl": "https://domain.com/docs/21d75dca2eec7b02080327f40220e20dxx2.pdf", # (Opzionale)
    
    "metadata": { # (Opzionale)
        "filters": {
            "id_collection": "id_collection_01",
            "id_series": "id_series_01",
            "id_client": "id_client_01",
            "id_user": "id_user_01",
            "id_workspace": "id_workspace_01"
        },
        "aditional_informatios": {
            "Collection Name:": "BetterAI Repo"
        }
    },

    "embedding_settings": { # (Opzionale)
        "llm_model": "text-embedding-3-large",
        "dimensions": 3072,
        "global_namespace": True,
        "batch_size": 200
    }
}



# Classe separata:
from decimal import Decimal
from copy import deepcopy


class BusinessPlanUsage:
    """
    Responsável por validar e atualizar o uso de créditos
    (USD e tokens) de um plano de negócio.

usage = BusinessPlanUsage(plan)

if usage.validate(operation):
    updated_plan = usage.update_usage(operation)
    """

    def __init__(self, plan: dict):
        # Trabalha sempre com cópia para evitar side-effects
        self.plan = deepcopy(plan)

    # ======================================================
    # VALIDATION
    # ======================================================
    def validate(self, operation: dict) -> bool:
        """
        Retorna True se o plano possuir créditos suficientes
        tanto em custo (USD) quanto em tokens.
        """

        # ===== CUSTO (USD) =====
        budget_usd = Decimal(
            self.plan["resorce"]["cost"]["monthly_budget_total_cost_usd"]
        )
        used_usd = Decimal(self.plan["cost"]["total_cost_usd"])
        operation_usd = Decimal(
            operation["embedding_cost"]["total_cost"]["cost_usd"]
        )

        has_usd_credit = (budget_usd - used_usd) >= operation_usd

        # ===== TOKENS =====
        budget_tokens = self.plan["resorce"]["tokens"]["monthly_budget_total_tokens"]
        used_tokens = self.plan["tokens"]["total_tokens"]
        operation_tokens = operation["embedding_cost"]["tokens"]

        has_token_credit = (budget_tokens - used_tokens) >= operation_tokens

        return has_usd_credit and has_token_credit

    # ======================================================
    # UPDATE
    # ======================================================
    def update_usage(self, operation: dict, validate: bool = True) -> dict:
        """
        Atualiza o uso de créditos do plano (USD e tokens)
        com base no custo da operação de embedding.

        Retorna o plano atualizado.
        """

        if validate and not self.validate(operation):
            raise ValueError("Créditos insuficientes para realizar a operação")

        # ===== VALORES DA OPERAÇÃO =====
        operation_usd = Decimal(
            operation["embedding_cost"]["total_cost"]["cost_usd"]
        )
        operation_tokens = int(operation["embedding_cost"]["tokens"])

        # ===== ATUALIZA CUSTO (USD) =====
        self.plan["cost"]["input_cost_usd"] = str(
            Decimal(self.plan["cost"]["input_cost_usd"]) + operation_usd
        )
        self.plan["cost"]["total_cost_usd"] = str(
            Decimal(self.plan["cost"]["total_cost_usd"]) + operation_usd
        )

        # ===== ATUALIZA TOKENS =====
        self.plan["tokens"]["input_tokens"] += operation_tokens
        self.plan["tokens"]["total_tokens"] += operation_tokens

        return self.plan



















class EmbeddingFile:

    def __init__(self, payload, file):

        self.payload = payload
        self.file = file

        self.metadata = payload["metadata"]
        self.embedding_settings = payload["embedding_settings"]

        self.mongo = MongoDBManager()


    def transform_embedding_data(self, file_extention, file_content):
        # Preparazione dei dati per l'embedding
        try:
            #logger.debug("Preparando dados para embeddings...")

            payload = self.payload

            embedding_content = {
                "file_name": "filename",
                "file_url": "https://test.com",
                "file_content": file_content
            }
            
            embedding_content.update(payload["metadata"]["aditional_informatios"])

            embedding_metadata = {
                "company_id": payload["company_id"],
                "file_id": payload["file_id"],
                "fileName": "fileName",
                "file_extention": file_extention,
                "fileUrl": payload["fileUrl"]
            }

            # Metadata filters
            embedding_metadata.update(payload["metadata"]["filters"])

            # Metadata aditional_informatios
            embedding_metadata.update(payload["metadata"]["aditional_informatios"])

            #logger.info("Dados para embedding preparados com sucesso.")

            return embedding_content, embedding_metadata

        except Exception as e:
            #logger.error("Erro ao transformar dados para embedding : %s. jobId: %s, fileId: %s", e, self.sqs_message_body["jobId"], self.sqs_message_body["fileId"])
            raise





    def embedding_cost(self, content):
        try:
            # Calcola i costi
            calc = EmbeddingCostCalculator(self.embedding_settings["llm_model"])
            cost = calc.calculate_cost_json(content)

            return {
                "embedding_cost": cost
            }

        except Exception as e:
            raise





    def embedding(self, embedding_content, embedding_metadata):
        try:
            # Si fa l'embedding
            pine_client = PineconeClient(index_name="backai-vectorstore", 
                                        namespace="test_namespace", global_namespace="global_namespace")
            
            pine_service = PineconeVectorService(pine_client, embedding_model_name=self.embedding_settings["llm_model"], 
                                                 dimensions=self.embedding_settings["dimensions"])

            response = pine_service.generate_vectors(
                text=str(embedding_content),
                metadata=embedding_metadata,
                save_global=self.embedding_settings["global_namespace"],
                batch_size=self.embedding_settings["batch_size"]
            )

            return response

        except Exception as e:
            raise





    def save_process(self, payload:dict, aggregates:list):
        # Salva l'operazione sul MongoDB
        for agg in aggregates:
            for key in agg.keys():
                payload[key] = agg[key]
        
        mongo_id = self.mongo.salvar_payload(database_name="embeddings", collection_name="betterai_embeddings", payload=payload)
        
        return mongo_id, payload








    def EmbeddingExecute(self):
        # Fluxo 
        # payload_validation
        # file_from_bytes -> filename, ext, file_bytes_io
        # extract_file_content -> text

        filename = "Candidatura.pdf"
        ext = "pdf"
        text = "Negli ultimi anni ho lavorato su diversi progetti in diversi settori, tra cui intelligenza artificiale"

        embedding_content, embedding_metadata = self.transform_embedding_data(
            payload=self.payload,
            file_extention=ext,
            file_content=text
        )
        
        #"""
        operation_cost = self.embedding_cost(content=str(embedding_content))

        business = self.mongo.buscar_documentos(database_name="TokensUsage",
                                        collection_name="BusinessAccountManage", 
                                        filtro={"business_id": "0011"})[0]
        
        updated_plan = BusinessPlanUsage(plan=business["plan"]).update_usage(operation=operation_cost)

        self.mongo.atualizar_documentos(
            database_name="TokensUsage", collection_name="BusinessAccountManage", 
            filtro={"business_id": "0011"}, novos_valores={"plan": updated_plan}
        )
        #"""

        vectorstore_embedding = self.embedding(str(embedding_content), embedding_metadata)
        mongo_id, mongo_payload = self.save_process(self.payload, [operation_cost, {"vectorstore_informations": vectorstore_embedding["embedding_informations"]}])

        response = {
            "status": "success",
            "message": "File embedded",
            "metadata": {
                "fileId": self.payload["file_id"],
                "mongoId": mongo_id,
            }
        }

        return response
        

embedding_module = EmbeddingFile(payload=payload, file="file")
embed = embedding_module.EmbeddingExecute()

print(embed)

























"""
python -m src.embedding.embedding_module

payload = {
    "status": "success",
    "message": "File embedded",
    "metadata": {
        "fileId": "21d75dca2eec7b02080327f40220e20dxx2.pdf",
        "mongoId": "83720083721",
    }
}
"""











