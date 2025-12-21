import json

payload = {
    # Prima parte (Obbligatorio)
    
    "company_id": "1",
    "file_id": "21d75dca2eec7b02080327f40220e20dxx2.pdf",
    "fileName": "name file.pdf",
    "fileUrl": "https://domain.com/docs/21d75dca2eec7b02080327f40220e20dxx2.pdf",

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

    "embedding_settingss": {
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

def validate_embedding_settings(payload: dict) -> bool:
    """
    Valida embedding_settings:
    - se NON esiste → True
    - se esiste:
        - deve essere un dict
        - deve contenere i campi obbligatori
        - valori NON None e NON stringhe vuote
    """
    if not isinstance(payload, dict):
        return False

    # embedding_settings è opzionale
    if "embedding_settings" not in payload:
        return True

    embedding_settings = payload.get("embedding_settings")

    if not isinstance(embedding_settings, dict):
        return False

    required_fields = (
        "llm_model",
        "dimensions",
        "global_namespace",
        "batch_size",
    )

    for field in required_fields:
        if field not in embedding_settings:
            return False

        value = embedding_settings[field]

        if value is None:
            return False

        if isinstance(value, str) and value.strip() == "":
            return False

    return True

is_valid = (
    validate_required_fields(payload)
    and validate_embedding_settings(payload)
)

print(is_valid)


# python -m src.embedding.tokens_calculator.test