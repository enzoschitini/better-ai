import json
import time

from copy import deepcopy

from src.tracing.tracing_core import ApplicationTracing
from src.database.no_relational_db.router import DocumentStore

from src.embedding.services.file_content_extractor import FileContentExtractor
from src.embedding.aggregates.aggregate_embedding_content import AggregateEmbeddingContent
from src.embedding.modules.config import GetConfig

from src.vector_store.pinecone.pinecone_client import PineconeClient
from src.vector_store.pinecone.pinecone_vectorstore_services import PineconeVectorService

from src.tokens_calculate.token_counter import TokenCounter
from src.tokens_calculate.model_pricing import ModelPricingFactory
from src.tokens_calculate.exchange_rate.exchange_rate import ExchangeRateService

from src.utils.unique_id_factory import IDGenerator
from src.utils.manager_process_informations import ManagerProcessInformations


tracer = ApplicationTracing(
    flag="Embedding File",
    file_name="embedding_file.py",
    log_file_name="embedding_file",
    show_info_logs=True
)

class EmbeddingFile(ManagerProcessInformations):
    def __init__(self, payload: dict | None):
        try:
            super().__init__()

            # Guarantee that payload is a valid dict
            payload = payload or {}

            # Deep copy to avoid external effects
            self.payload = deepcopy(payload)

            if not self.payload.get("job_id"):
                raise ValueError("Missing required field: job_id")

            # Normaliza estrutura base
            self.payload.setdefault("vector_db_settings", {})
            self.payload.setdefault("identifiers", {})
            self.payload.setdefault("file_info", {})
            self.payload.setdefault("embedding_metadata", {})
            self.payload.setdefault("pipeline", None)

            # Get default config values
            config = GetConfig()
            self.config = config.embedding_file()

            # Merge vector_db_settings with config
            self.payload["vector_db_settings"] = {
                **self.config["vector_db_settings"],
                **self.payload.get("vector_db_settings", {})
            }

            # Ensure minimum identifiers
            identifiers = self.payload["identifiers"]

            if not identifiers.get("file_id"):
                id_generator = IDGenerator()
                identifiers["file_id"] = id_generator.timestamp()

            self.payload["identifiers"] = identifiers

            # Minimum file_info validation (optional but recommended)
            file_info = self.payload["file_info"]

            required_file_fields = ["name", "extension", "bytes"]
            missing_fields = [f for f in required_file_fields if f not in file_info]

            if missing_fields:
                raise ValueError(f"Missing required file_info fields: {missing_fields}")
            
            self.vector_db_settings = self.payload["vector_db_settings"]
            self.main_namespace = self.vector_db_settings.get("main_namespace")
            self.global_namespace = self.vector_db_settings.get("global_namespace")

            self.database_name=self.config["database_name"]
            self.collection_name=self.config["collection_name"]

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

    def _get_vector_db(self):
        try:
            self.pine_client = PineconeClient(
                index_name=self.vector_db_settings.get("index_name"),
                main_namespace=self.vector_db_settings.get("main_namespace"),
                global_namespace=self.vector_db_settings.get("global_namespace", None),
                embedding_model=self.vector_db_settings.get("model")
            )

            self.pine_service = PineconeVectorService(
                vector_client=self.pine_client,
                embedding_model_name=self.vector_db_settings.get("model"), 
                dimensions=self.vector_db_settings.get("dimensions")
            )

        except Exception as e:
            raise RuntimeError(f"Failed to load vector store database: {str(e)}")
    
    def _rollback_vector_store(self):
        try:
            tracer.ERROR("Error saving process metadata, initiating rollback.")

            delete_main_namespace = self.pine_service.delete_documents(
                target_feature="file_id", 
                target_id=self.payload["identifiers"]["file_id"], 
                namespace=self.main_namespace
            )

            time.sleep(1)

            delete_global_namespace = self.pine_service.delete_documents(
                target_feature="file_id", 
                target_id=self.payload["identifiers"]["file_id"], 
                namespace=self.global_namespace
            )

            delete = {
                "main_namespace": delete_main_namespace,
                "global_namespace": delete_global_namespace
            }

            tracer.INFO("Rollback completed successfully.")

            self.add("roolback_vector_db", delete)
            return delete

        except Exception as e:
            raise RuntimeError(f"Failed to rollback vector store: {str(e)}")   

    def extract_file_content(self, file_extension: str, file_bytes: bytes) -> str:
        try:
            tracer.INFO("Extracting content from the file")
            extractor = FileContentExtractor(file_bytes, file_extension)
            result = extractor.extract()

            file_content = result["file_content"]
            self.add("file_content", file_content)

            tracer.INFO("Content extracted successfully.")
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
                tracer.INFO("Process the pipeline to generate additional content")
                aggregate_content = AggregateEmbeddingContent(pipeline)
                additional_content = aggregate_content.process()
            
            prepared_content = {
                "file_content": file_content,
                **(additional_content if pipeline else {})
            }

            prepared_metadata = {
                **identifiers,
                "file_name": file_info["name"],
                "file_extension": file_info["extension"],
                **(embedding_metadata or {})
            }

            self.add("embedding_content", prepared_content)
            self.add("embedding_metadata", prepared_metadata)

            tracer.INFO("prepared_content and prepared_metadata were successfully generated.")

            return prepared_content, prepared_metadata

        except Exception as e:
            raise RuntimeError(f"Failed to build embedding payload: {str(e)}")

    def calculate_usage_summary(self, model: str, prepared_content: dict) -> dict:
        try:
            tracer.INFO("Collecting dollar exchange rate")
            exchange_service = ExchangeRateService()
            usd_rate = exchange_service.get_usd_rate()

            parts_cost_info = {}

            for key, value in prepared_content.items():
                tracer.INFO("Calculating the cost for the parties")
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

            tracer.INFO("Usage summary calculated successfully.")
            return usage_summary 

        except Exception as e:
            raise RuntimeError(f"Failed to calculate usage summary: {str(e)}")     

    def store_embeddings(self, embedding_content: str, embedding_metadata: dict, flags: dict = None):
        try:
            if flags:
                tracer.INFO("Add the flags to the metadata")
                embedding_metadata = {**embedding_metadata, **flags}
            
            tracer.INFO("Performing embedding")
            
            embed_response = self.pine_service.generate_vectors(
                text=embedding_content,
                metadata=embedding_metadata,
                save_global=self.vector_db_settings.get("save_global", False),
                batch_size=self.vector_db_settings.get("batch_size", 200),
            )

            self.add("embedding_response", embed_response)
            tracer.INFO("Embedding successfully completed.")
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
            #erro = 1 / 0

            save_payload = self.payload.copy()
            save_payload["file_info"].pop("bytes", None)
            save_payload["usage_summary"] = usage_summary 
            save_payload["embedding_response"] = embed_response

            save_response = manager.save_payload(
                database_name=self.database_name,
                collection_name=self.collection_name,
                payload=save_payload
            )

            self.add("save_response", save_response)
            tracer.INFO("Process metadata saved successfully.")
            return save_response

        except Exception as e:
            delete = self._rollback_vector_store()
            tracer.ERROR(f"Rollback executed: {delete}")

            raise RuntimeError(f"Failed to save process metadata: {str(e)}")

    def run(self):
        try:
            tracer.INFO("Embedding started...")

            file_content = self.extract_file_content(
                self.payload["file_info"]["extension"], 
                self.payload["file_info"]["bytes"]
            )

            prepared_content, prepared_metadata = self.build_embedding_payload(
                identifiers=self.payload["identifiers"],
                file_info=self.payload["file_info"],
                file_content=file_content,
                embedding_metadata=self.payload["embedding_metadata"],
                pipeline=self.payload["pipeline"]
            )

            usage_summary = self.calculate_usage_summary(
                model=self.payload["vector_db_settings"]["model"], 
                prepared_content=prepared_content
            )

            embed_response = self.store_embeddings(
                embedding_content=json.dumps(prepared_content),
                embedding_metadata=prepared_metadata
            )

            self.save_process_metadata(
                usage_summary=usage_summary,
                embed_response=embed_response
            )

            tracer.INFO("Embedding flow completed successfully.")

            return {
                "job_id": self.payload.get("job_id"),
                "file_id": self.payload.get("identifiers", {}).get("file_id")
            }

        except Exception as e:
            raise RuntimeError(f"Embedding process execution failed: {str(e)}")
