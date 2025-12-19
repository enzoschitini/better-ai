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
from src.embedding.tokens_calculator.business_plan_usage import BusinessPlanUsage

load_dotenv()



payload = {
    "company_id": "1",
    "file_id": "21d75dca2eec7b02080327f40220e20dxx2.pdf",
    "fileName": "name file.pdf",
    "fileUrl": "https://domain.com/docs/21d75dca2eec7b02080327f40220e20dxx2.pdf",
    
    "metadata": {
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

    "embedding_settings": {
        "llm_model": "text-embedding-3-large",
        "dimensions": 3072,
        "global_namespace": True,
        "batch_size": 200
    }
}




class EmbeddingFile:
    """
    Docstring per EmbeddingFile
    """
    def __init__(self, payload, file):

        self.payload = payload
        self.file = file

        self.metadata = payload["metadata"]
        self.embedding_settings = payload["embedding_settings"]

        self.mongo = MongoDBManager()


    def file_from_bytes(self, file): # 2. Transforma l'archivio in BitesIO
        """
        Recebe um UploadFile (FastAPI),
        valida a extensão e retorna:
        - filename
        - extensão
        - BytesIO
        """

        ALLOWED_EXTENSIONS = {
            "txt", "md", "markdown", "html",
            "pdf", "doc", "docx", "ppt", "pptx",
            "csv", "xls", "xlsx", "xml", "json"
        }

        # Nome do arquivo
        filename = file.filename

        if not filename or "." not in filename:
            raise ValueError("Nome de arquivo inválido")

        # Extensão
        ext = filename.lower().split(".")[-1]

        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Extensão não suportada: .{ext}")

        # Lê os bytes do UploadFile
        file_bytes = file.file.read()

        if not file_bytes:
            raise ValueError("Arquivo vazio")

        # Converte para BytesIO
        file_bytes_io = BytesIO(file_bytes)

        return filename, ext, file_bytes_io

    def extract_file_content(self, file_bytes, file_extension):
        # 3. Estrarre il contenuto
        """
        Carrega arquivo → transforma em BytesIO → extrai conteúdo
        """
        try:
            extractor = FileContentExtractor(file_bytes, file_extension)
            return extractor.extract()

        except Exception as e:
            filename = "filename"
            print(f"❌ Error processing file '{filename}': {e}")
            raise

    def transform_embedding_data(self, payload, file_extention, file_content):
        # Preparazione dei dati per l'embedding
        try:
            #logger.debug("Preparando dados para embeddings...")

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





    def embedding_cost(self, embedding_content):
        try:
            # Calcola i costi
            database_name="TokensUsage"
            collection_name="BusinessAccountManage"
            embedding_content = str(embedding_content)

            calc = EmbeddingCostCalculator(self.embedding_settings["llm_model"])
            operation_cost = {"embedding_cost": calc.calculate_cost_json(embedding_content)}

            business = self.mongo.buscar_documentos(database_name, collection_name, {"business_id": "0011"})[0]
            
            updated_plan = BusinessPlanUsage(plan=business["plan"]).update_usage(operation=operation_cost)

            if updated_plan == "not_credits":
                return "not_credits"
            
            else:
                self.mongo.atualizar_documentos(database_name, collection_name, {"business_id": "0011"}, {"plan": updated_plan})

                return {
                    "embedding_cost": operation_cost
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
        
        return mongo_id




    def EmbeddingExecute(self):
        # Fluxo 
        # payload_validation
        # file_from_bytes -> filename, ext, file_bytes_io
        # extract_file_content -> text

        filename = "Candidatura.pdf"
        ext = "pdf"
        text = "Negli ultimi anni ho lavorato su diversi progetti in diversi settori, tra cui intelligenza artificiale"

        embedding_content, embedding_metadata = self.transform_embedding_data(payload=self.payload, file_extention=ext, file_content=text)
        
        #"""
        operation_cost = self.embedding_cost(content=embedding_content)

        vectorstore_embedding = self.embedding(str(embedding_content), embedding_metadata)
        mongo_id = self.save_process(self.payload, [operation_cost, {"vectorstore_informations": vectorstore_embedding["embedding_informations"]}])

        response = {
            "status": "success",
            "message": "File embedded",
            "metadata": {
                "fileId": self.payload["file_id"],
                "mongoId": mongo_id,
            }
        }

        return response


"""
embedding_module = EmbeddingFile(payload=payload, file="file")
embed = embedding_module.EmbeddingExecute()

print(embed)
"""

























"""
python -m src.embedding.embedding_module
"""











