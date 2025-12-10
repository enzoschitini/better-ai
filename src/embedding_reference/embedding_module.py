import os
import logging
from dotenv import load_dotenv
from datetime import datetime

from src.knowledge_base.s3_file_downloader import FileDownloader, HttpURLValidator
from src.knowledge_base.file_content_extractor import FileContentExtractor
from src.knowledge_base.pinecone_vector_store import PineconeClient, PineconeVectorService
from src.knowledge_base.redis_status import RedisStatus, FileStatus
from src.knowledge_base.file_content_extractor import PromptManager
from src.knowledge_base.send_mongo import save_process
from src.knowledge_base.sqs_client import SQSClient

# configuração básica do logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class EmbeddingFile:
    # classe que processa o arquivo completo, recebendo o sqs_message_body

    def __init__(self, sqs_message_body):
        # armazena a mensagem e inicializa o Redis
        self.sqs_message_body = sqs_message_body
        self.redis = RedisStatus(sqs_message_body["fileId"])

        # monta a URL completa do arquivo no S3
        load_dotenv()
        self.FILE_URL = f"{os.getenv('S3_DOMAIN')}{sqs_message_body['fileUrl']}"

        logger.info("Serviço de embedding iniciado para o JobID: %s", sqs_message_body["jobId"])

    def extract_file_content(self):
        # etapa responsável por baixar e extrair o conteúdo
        try:
            logger.debug("Baixando arquivo da URL: %s", self.FILE_URL)

            downloader = FileDownloader(url_validator=HttpURLValidator())
            file_bytes, file_extension = downloader.download(self.FILE_URL)

            logger.info("Download concluído. Extensão identificada: %s", file_extension)

            self.redis.update_status("PROCESSING")

            self.redis.publish_status(
                file_id=self.sqs_message_body["fileId"],
                status=FileStatus.PROCESSING,
                channel=f"job_updates:{self.sqs_message_body["jobId"]}"
            )

        except Exception as e:
            logger.error("Erro ao fazer download do arquivo: %s. jobId: %s, fileId: %s", e, self.sqs_message_body["jobId"], self.sqs_message_body["fileId"])
            self.redis.update_status("FAILED")

            self.redis.publish_status(
                file_id=self.sqs_message_body["fileId"],
                status=FileStatus.FAILED,
                channel=f"job_updates:{self.sqs_message_body["jobId"]}"
            )

            raise

        try:
            logger.debug("Extraindo conteúdo do arquivo...")
            extractor = FileContentExtractor(file_bytes, file_extension)
            result = extractor.extract()
            logger.info("Extração concluída com sucesso.")

        except Exception as e:
            logger.error("Erro ao extrair conteúdo do arquivo: %s. jobId: %s, fileId: %s", e, self.sqs_message_body["jobId"], self.sqs_message_body["fileId"])
            self.redis.update_status("FAILED")

            self.redis.publish_status(
                file_id=self.sqs_message_body["fileId"],
                status=FileStatus.FAILED,
                channel=f"job_updates:{self.sqs_message_body["jobId"]}"
            )

            raise

        return result, file_extension

    def transform_embedding_data(self, file_process, file_extension):
        # etapa que monta os dados do embedding
        try:
            logger.debug("Preparando dados para embeddings...")

            if "usage_metadata" in file_process.get("response", {}):
                file_content = file_process["response"]["file_content"]
                logger.debug("Uso de metadata detectado: %s", file_process["response"]["usage_metadata"])
            else:
                file_content = file_process["response"]

            embedding_content = {
                "file_name": self.sqs_message_body["metadata"]["st_name"],
                "file_url": f"{os.getenv('S3_DOMAIN')}{self.sqs_message_body['fileUrl']}",
                "file_content": file_content
            }

            embedding_metadata = {
                "file_id": self.sqs_message_body["fileId"],
                "collection_id": self.sqs_message_body["metadata"]["id_collection"],
                "serie_id": self.sqs_message_body["metadata"]["id_series"],
                "client_id": self.sqs_message_body["metadata"]["id_client"],
                "user_id": self.sqs_message_body["metadata"]["id_user"],
                "workspace_id": self.sqs_message_body["metadata"]["id_workspace"]
            }

            logger.info("Dados para embedding preparados com sucesso.")

        except Exception as e:
            logger.error("Erro ao transformar dados para embedding : %s. jobId: %s, fileId: %s", e, self.sqs_message_body["jobId"], self.sqs_message_body["fileId"])
            self.redis.update_status("FAILED")

            self.redis.publish_status(
                file_id=self.sqs_message_body["fileId"],
                status=FileStatus.FAILED,
                channel=f"job_updates:{self.sqs_message_body["jobId"]}"
            )

            raise

        return embedding_content, embedding_metadata

    def send_to_pinecone(self, embedding_content, embedding_metadata):
        # etapa final que envia os dados para o Pinecone
        try:
            logger.debug("Enviando dados para o Pinecone...")

            pine_client = PineconeClient()
            pine_service = PineconeVectorService(pine_client)

            response = pine_service.generate_vectors(
                text=str(embedding_content),
                metadata=embedding_metadata,
                save_global=True,
                batch_size=200
            )

            logger.info("Dados enviados para o Pinecone com sucesso.")

        except Exception as e:
            logger.error("Erro ao gerar ou enviar embeddings ao Pinecone : %s. jobId: %s, fileId: %s", e, self.sqs_message_body["jobId"], self.sqs_message_body["fileId"])
            self.redis.update_status("FAILED")

            self.redis.publish_status(
                file_id=self.sqs_message_body["fileId"],
                status=FileStatus.FAILED,
                channel=f"job_updates:{self.sqs_message_body["jobId"]}"
            )

            raise

        return response

    def run(self):
        start_time = datetime.now()
        
        # método principal que executa todas as etapas
        logger.info("Iniciando pipeline completo de processamento...")

        file_process, file_extension = self.extract_file_content()

        embedding_content, embedding_metadata = self.transform_embedding_data(
            file_process,
            file_extension
        )

        embedding_response = self.send_to_pinecone(
            embedding_content,
            embedding_metadata
        )

        response = self.sqs_message_body

        mongo_payload = {
            "job_id": response["jobId"],
            "metadata": response["metadata"],
            "processing_info": {
                "file_extension": file_extension,
                "output_gerado": str(embedding_content)
            },

            "file_info": {
                "fileId": response["fileId"],
                "fileUrl": response["fileUrl"]
            },
            "start_time": start_time,
            "end_time": None
        }
        image_extensions = {"jpg", "jpeg", "png", "webp", "gif"}
        audio_extensions = {"mp3", "wav", "flac", "aac", "m4a", "wma"}

        all_extensions = image_extensions | audio_extensions

        if file_extension.lower() in all_extensions:
            usage_metadata = file_process["response"]["usage_metadata"]

            js_metadata = {
            "description": embedding_content["file_content"]
            }

            response["metadata"]["js_metadata"] = js_metadata

            if file_extension.lower() in image_extensions:
                prompt = PromptManager.get_prompt("image_prompt")

            elif file_extension.lower() in audio_extensions:
                prompt = PromptManager.get_prompt("audio_prompt")

            mongo_payload["processing_info"]["prompt"] = prompt
            mongo_payload["processing_info"]["modelo_extracao"] = "gemini-1.5-pro"
            mongo_payload["processing_info"]["input_tokens"] = usage_metadata["prompt_token_count"]
            mongo_payload["processing_info"]["output_tokens"] = usage_metadata["candidates_token_count"]
        

        end_time = datetime.now()
        mongo_payload["end_time"] = end_time

        """ final_status = self.redis.update_status("SUCCEEDED")

        self.redis.publish_status(
            file_id=self.sqs_message_body["fileId"],
            status=FileStatus.SUCCEEDED,
            channel=f"job_updates:{self.sqs_message_body["jobId"]}"
        ) """

        response["metadata"]["st_process_status"] = "SUCCEEDED"
        mongo_id = save_process(payload=mongo_payload)

        # Retornar os dados para o S3sync
        client_sqs = SQSClient()

        client_sqs.send_message(
            message_body=response,
            message_group_id=response["jobId"]
        )

        logger.info("Processamento completo finalizado. jobId: %s, fileId: %s", self.sqs_message_body["jobId"], self.sqs_message_body["fileId"])
        return response
    