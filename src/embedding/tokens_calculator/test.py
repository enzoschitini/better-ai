import json

payload = {
    # Prima parte (Obbligatorio)
    
    "company_id": "1",
    "file_id": "21d75dca2eec7b02080327f40220e20dxx2.pdf",
    "fileName": "name file.pdf",
    "fileUrl": "",

    # Metadata (Non è obbligatorio)
    
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

    # Embedding Settings (Non è obbligatorio)

    "embedding_settings": {
        "llm_model": "text-embedding-3-large",
        "dimensions": 3072,
        "global_namespace": True,
        "batch_size": 200
    }
}

def validate_required_fields(payload: dict) -> bool:
    """
    Valida la prima parte obbligatoria del payload:
    - campo presente
    - valore NON None
    - valore NON stringa vuota
    """
    required_fields = (
        "company_id",
        "file_id",
        "fileName",
        "fileUrl",
    )

    if not isinstance(payload, dict):
        return False

    for field in required_fields:
        if field not in payload:
            return False

        value = payload[field]

        if value is None:
            return False

        if isinstance(value, str) and value.strip() == "":
            return False

    return True


print(validate_required_fields(payload=payload))


# python -m src.embedding.tokens_calculator.test