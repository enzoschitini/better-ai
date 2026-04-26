import json

from io import BytesIO
from src.embedding.modules.embedding_file import EmbeddingFile

def generate_payload(view: bool = False):
    with open("doc/test files/Candidatura.pdf", "rb") as f:
        file_bytes = BytesIO(f.read())
    
    if view:
        file_bytes = file_bytes[:20]

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
            "bytes": file_bytes
        }
    }

    if view:
        print(json.dumps(payload, indent=4, default=str))

    return payload



payload = generate_payload()

embedder = EmbeddingFile(payload)
embedder._init_tracking()
embedder.run()
embedder.save()

# Step 1: Configure and validate the payload
# Step 2: Download the file from the provided URL
# Step 3: Extract content from the file
# Step 4: Generate embedding payload
# Step 5: Calculate cost
# Step 6: Embedding content and store vectors
# Step 7: Save process
# Step 8: Delete temporary files and clean up resources
# Step 9: Return response with embedding information and cost details

# python -m src.embedding.test