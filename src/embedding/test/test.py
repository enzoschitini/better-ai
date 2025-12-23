import json

payload = {
    "client_id": "1",
    "fileId": "21d75dca2eec7b02080327f40220e20dxx2.pdf",
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

def transform_embedding_data(payload, file_extention, file_content):
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
            "client_id": payload["client_id"],
            "fileId": payload["fileId"],
            "fileName": payload["fileName"],
            "file_extention": file_extention,
            "fileUrl": payload["fileUrl"],
            "metadata": payload["metadata"]
        }

        #logger.info("Dados para embedding preparados com sucesso.")

        return embedding_content, embedding_metadata

    except Exception as e:
        #logger.error("Erro ao transformar dados para embedding : %s. jobId: %s, fileId: %s", e, self.sqs_message_body["jobId"], self.sqs_message_body["fileId"])
        raise

embedding_content, embedding_metadata = transform_embedding_data(
    payload=payload,
    file_extention="pdf",
    file_content="ndndndndndndndndnd"
)

print(json.dumps(embedding_content, indent=4))
print(json.dumps(embedding_metadata, indent=4))
