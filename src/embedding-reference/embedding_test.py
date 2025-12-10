from src.embedding-reference.file_content_extractor import FileContentExtractor



def extract_file_content():
    try:
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



