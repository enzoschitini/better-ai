import json
from io import BytesIO
from copy import deepcopy

from src.embedding.services.file_content_extractor import FileContentExtractor
from src.embedding.aggregates.aggregate_embedding_content import AggregateEmbeddingContent
from src.utils.manager_process_informations import ManagerProcessInformations

from src.vector_store.pinecone.pinecone_vectorstore_services import PineconeVectorService
from src.database.no_relational_db.router import DocumentStore

from src.tokens_calculate.token_counter import TokenCounter
from src.tokens_calculate.model_pricing import ModelPricingFactory
from src.tokens_calculate.exchange_rate.exchange_rate import ExchangeRateService

from src.utils.unique_id_factory import IDGenerator

CONFIG = {
    "embedding_settings": {
        "model": "text-embedding-3-large",
        "dimensions": 3072,
        "chunk_size": 500,
        "chunk_overlap": 50,
        "normalize": True,
        "save_global": False,
        "batch_size": 200,
    },

    "pinecone_namespace": "embed_module",

    "database_name": "embedding_db",
    "collection_name": "embedding_processes"
}

class EmbeddingFile(ManagerProcessInformations):
    def __init__(self, payload: dict | None):
        try:

            super().__init__()

            # Garante que payload é um dict válido
            payload = payload or {}

            # Deep copy para evitar efeitos colaterais externos
            self.payload = deepcopy(payload)

            if not self.payload.get("job_id"):
                raise ValueError("Missing required field: job_id")

            # 🔹 Normaliza estrutura base
            self.payload.setdefault("embedding_settings", {})
            self.payload.setdefault("identifiers", {})
            self.payload.setdefault("file_info", {})
            self.payload.setdefault("embedding_metadata", {})
            self.payload.setdefault("pipeline", None)

            # 🔹 Merge de embedding_settings com CONFIG
            self.payload["embedding_settings"] = {
                **CONFIG["embedding_settings"],
                **self.payload.get("embedding_settings", {})
            }

            # 🔹 Garantir identifiers mínimo
            identifiers = self.payload["identifiers"]

            if not identifiers.get("file_id"):
                id_generator = IDGenerator()
                identifiers["file_id"] = id_generator.timestamp()

            self.payload["identifiers"] = identifiers

            # 🔹 Validação mínima de file_info (opcional mas recomendado)
            file_info = self.payload["file_info"]

            required_file_fields = ["name", "extension", "bytes"]
            missing_fields = [f for f in required_file_fields if f not in file_info]

            if missing_fields:
                raise ValueError(f"Missing required file_info fields: {missing_fields}")
            
            self.pinecone_namespace=CONFIG["pinecone_namespace"]
            self.database_name=CONFIG["database_name"]
            self.collection_name=CONFIG["collection_name"]

            self._get_vector_db()

        except Exception as e:
            raise RuntimeError(f"Failed to initialize EmbeddingFile: {str(e)}")

    def _init_tracking(self):
        try:
            self.start()
            self.add("payload", self.payload)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize tracking: {str(e)}")

    def _calculate_usage(self, model: str, content: str) -> dict:
        try:
            pricing = ModelPricingFactory.create(model)
            counter = TokenCounter(model)

            tokens = counter.count(content)
            cost = pricing.cost(tokens)

            return {
                "caracter_count": len(content),
                "tokens": tokens,
                "cost_usd": f"{cost:.6f}"
            }
        except Exception as e:
            raise RuntimeError(f"Failed to calculate usage: {str(e)}")

    def extract_file_content(self, file_extension: str, file_bytes: bytes) -> str:
        try:
            extractor = FileContentExtractor(file_bytes, file_extension)
            result = extractor.extract()

            file_content = result["file_content"]
            self.add("file_content", file_content)

            return file_content

        except Exception as e:
            raise RuntimeError(f"Failed to extract file content: {str(e)}")
    
    def build_embedding_payload(
        self,
        identifiers: dict,
        file_info: dict,
        file_content: str,
        embedding_metadata: dict = None,
        pipeline: dict = None,
    ):  
        try:
            if pipeline:
                # Processar o pipeline para gerar conteúdo adicional
                aggregate_content = AggregateEmbeddingContent(pipeline)
                additional_content = aggregate_content.process()
            
            prepared_content = {
                "file_content": file_content,
                **(additional_content if pipeline else {})
            }

            prepared_metadata = {
                **identifiers,  # espalha tudo aqui
                "file_name": file_info["name"],
                "file_extension": file_info["extension"],
                **(embedding_metadata or {})  # evita erro se for None
            }

            self.add("embedding_content", prepared_content)
            self.add("embedding_metadata", prepared_metadata)

            return prepared_content, prepared_metadata

        except Exception as e:
            raise RuntimeError(f"Failed to build embedding payload: {str(e)}")

    def calculate_usage_summary(self, model: str, prepared_content: dict) -> dict:
        try:
            exchange_service = ExchangeRateService()
            usd_rate = exchange_service.get_usd_rate()

            parts_cost_info = {}

            for key, value in prepared_content.items():
                parts_cost_info[key] = self._calculate_usage(model, value)

            total_caracter_count = sum(part["caracter_count"] for part in parts_cost_info.values())
            total_tokens = sum(part["tokens"] for part in parts_cost_info.values())
            total_cost_usd = f"{sum(float(part['cost_usd']) for part in parts_cost_info.values()):.6f}"

            usage_summary = {
                "total_caracter_count": total_caracter_count,
                "total_tokens": total_tokens,
                "total_cost_usd": total_cost_usd,
                "exchange_rate": usd_rate
            }

            if len(parts_cost_info) > 1:
                usage_summary["parts"] = parts_cost_info

            self.add("usage_summary", usage_summary)
            return usage_summary 

        except Exception as e:
            raise RuntimeError(f"Failed to calculate usage summary: {str(e)}")
    
    def _get_vector_db(self):
        try:
            self.pine_service = PineconeVectorService(
                embedding_model_name=self.payload["embedding_settings"]["model"], 
                dimensions=self.payload["embedding_settings"]["dimensions"]
            )

        except Exception as e:
            raise RuntimeError(f"Failed to load vector store database: {str(e)}")
    
    def _roolback_vector_db(self):
        try:
            delete = self.pine_service.delete_documents(
                target_feature="file_id", 
                target_id=self.payload["identifiers"]["file_id"], 
                namespace=self.pinecone_namespace
            )
            # {'deleted_vectors': 134, 'namespace': 'embed_module'}
            # {'deleted_vectors': 0}
            print(delete)
        except Exception as e:
            raise RuntimeError(f"Failed to delete vectors: {str(e)}")        

    def store_embeddings(self, embedding_content: str, embedding_metadata: dict, flags: dict = None):
        try:
            if flags:
                embedding_metadata = {**embedding_metadata, **flags}  # Adiciona as flags aos metadados
            
            
            embed_response = self.pine_service.generate_vectors(
                text=embedding_content,
                metadata=embedding_metadata,
                save_global=self.payload["embedding_settings"]["save_global"],
                batch_size=self.payload["embedding_settings"]["batch_size"]
            )
            """

            embed_response = {
                "status": "success",
                "message": "Embeddings saved successfully.",
                "embedding_informations": {
                    "namespace_main": "embed_module",
                    "namespace_global": None,
                    "batch_count": 1,
                    "chunks_ids": [
                        "64e871d9-0bab-417c-b3af-d037a7d0d8e5",
                        "da7fada9-3aad-4d7f-826c-c3021276d72e",
                        "80430b5f-6ed6-4d28-90d4-6a9d6eb78528",
                        "ea004fc4-4a40-4434-8cb6-9736756ced8d",
                        "b60c1e81-3424-4fdc-a743-250eb320eba1",
                        "83e486be-1244-4d97-9325-1f0d3e921a27"
                    ]
                }
            }
            """

            self.add("embedding_response", embed_response)
            return embed_response

        except Exception as e:
            raise RuntimeError(f"Failed to store embeddings: {str(e)}")

    def save_process_metadata(
        self,
        usage_summary: dict,
        embed_response: dict
    ):
        try:
            manager = DocumentStore()

            save_payload = self.payload.copy()
            save_payload["file_info"].pop("bytes", None)
            save_payload["usage_summary"] = usage_summary 
            save_payload["embedding_response"] = embed_response

            #print(f"\nsave_payload: {json.dumps(save_payload, indent=4)}")

            save_response = manager.save_payload(
                database_name=self.database_name,
                collection_name=self.collection_name,
                payload=save_payload
            )

            self.add("save_response", save_response)
            return save_response

        except Exception as e:
            # Delete vectores
            self._roolback_vector_db()
            self.save()
            raise RuntimeError(f"Failed to save process metadata: {str(e)}")

    def run(self):
        try:
            file_content = self.extract_file_content(self.payload["file_info"]["extension"], self.payload["file_info"]["bytes"])

            prepared_content, prepared_metadata = self.build_embedding_payload(
                identifiers=self.payload["identifiers"],
                file_info=self.payload["file_info"],
                file_content=file_content,
                embedding_metadata=self.payload["embedding_metadata"],
                pipeline=self.payload["pipeline"]
            )

            usage_summary = self.calculate_usage_summary(
                model=self.payload["embedding_settings"]["model"], 
                prepared_content=prepared_content
            )

            embed_response = self.store_embeddings(
                embedding_content=json.dumps(prepared_content),
                embedding_metadata=prepared_metadata,
                flags={"group": "test_group"}
            )

            self.save_process_metadata(
                usage_summary=usage_summary,
                embed_response=embed_response
            )

            return {
                "job_id": self.payload.get("job_id"),
                "file_id": self.payload.get("identifiers", {}).get("file_id")
            }

        except Exception as e:
            raise RuntimeError(f"Embedding process execution failed: {str(e)}")








def generate_payload():
    with open("doc/test files/Candidatura.pdf", "rb") as f:
        file_bytes = BytesIO(f.read())

    payload = {
        "job_id": "job_12345",

        "identifiers": {
            "client_id": "client_abc",
            "workspace_id": "workspace_001",
            "user_id": "user_789",
            "file_id": "file_xyz" # Può essere creato
        },

        "pipeline": {
            "generate_tags": True,
        },

        "embedding_metadata": {
            "source": "uploaded_file",
            "origin": "web_app",
            "language": "en",
            "tags": "#finance, #report, #2026"
        },

        "embedding_settings": {
            "model": "text-embedding-3-large",
            "dimensions": 3072,
            "chunk_size": 500,
            "chunk_overlap": 50,
            "normalize": True,
            "save_global": False,
            "batch_size": 200,
        },

        "file_info": {
            "name": "example.pdf",
            "extension": "pdf",
            "mime_type": "application/pdf",
            "size_bytes": 204800,
            "size_kb": 200,
            "size_mb": 0.2,
            "bytes": file_bytes#[:20]
        }
    }

    #print(json.dumps(payload, indent=4, default=str))

    return payload



payload = generate_payload()

embedder = EmbeddingFile(payload)
embedder._init_tracking()
embedder.run()
embedder.save()  # Salva o estado completo do processo em um arquivo JSON


    # Step 1: Configure and validate the payload
    # Step 2: Download the file from the provided URL
    # Step 3: Extract content from the file
    # Step 4: Generate embedding payload
    # Step 5: Calculate cost
    # Step 6: Embedding content and store vectors
    # Step 7: Save process
    # Step 8: Delete temporary files and clean up resources
    # Step 9: Return response with embedding information and cost details

#   