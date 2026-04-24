import json

from io import BytesIO

from src.embedding.services.file_content_extractor import FileContentExtractor

class AggregateEmbeddingContent:
    def __init__(self, pipeline):
        self.pipeline = pipeline

    def process(self):
        return {
            "additional_content": "This is additional content generated from the pipeline.",
            "generated_tags": "#finance, #report, #2026"
        }
    
class EmbeddingFile:
    def __init__(self, payload: dict):
        self.payload = payload
    

    def extract_content(self, file_extension: str, file_bytes: bytes) -> str:
        try:
            print(f"Extracting content from file with extension: {file_extension}")
            extractor = FileContentExtractor(file_bytes, file_extension)
            result = extractor.extract()
        except Exception as e:
            raise RuntimeError(f"Error extracting content: {str(e)}")
        
        print(f"Extracted content length: {len(result['file_content'])} characters")
        return result["file_content"]
    
    def generate_embedding_payload(
        self,
        identifiers: dict, # Em __init__ trata adicionando pelo menos file_id
        file_info: dict,
        file_content: str,
        embedding_metadata: dict = None,
        pipeline: dict = None,
    ):  
        if pipeline:
            # Processar o pipeline para gerar conteúdo adicional
            aggregate_content = AggregateEmbeddingContent(pipeline)
            additional_content = aggregate_content.process()
        
        final_embedding_content = {
            "file_content": file_content,
            **(additional_content if pipeline else {})
        }

        final_embedding_metadata = {
            **identifiers,  # espalha tudo aqui
            "file_name": file_info["name"],
            "file_extension": file_info["extension"],
            **(embedding_metadata or {})  # evita erro se for None
        }
        
        return final_embedding_content, final_embedding_metadata

    # Step 1: Configure and validate the payload
    # Step 2: Download the file from the provided URL
    # Step 3: Extract content from the file
    # Step 4: Generate embedding payload
    # Step 5: Calculate cost
    # Step 6: Embedding content and store vectors
    # Step 7: Save process
    # Step 8: Delete temporary files and clean up resources
    # Step 9: Return response with embedding information and cost details

# Carregar um arquivo

def generate_payload():
    with open("doc/test files/Candidatura.pdf", "rb") as f:
        file_bytes = BytesIO(f.read())

    payload = {
        "job_id": "job_12345",

        "identifiers": {
            "client_id": "client_abc",
            "workspace_id": "workspace_001",
            "user_id": "user_789",
            "file_id": "file_xyz"
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
            "model": "text-embedding-3-small",
            "dimensions": 1536,
            "chunk_size": 500,
            "chunk_overlap": 50,
            "normalize": True
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

    return payload

payload = generate_payload()
#print(json.dumps(payload, indent=4, default=str))

embedder = EmbeddingFile(payload)
#extract_content_data = embedder.extract_content(payload["file_info"]["extension"], payload["file_info"]["bytes"])

final_embedding_content, final_embedding_metadata = embedder.generate_embedding_payload(
    identifiers=payload["identifiers"],
    file_info=payload["file_info"],
    file_content="This is the extracted content from the file. It can be very long, so we will only use a snippet for embedding.",
    embedding_metadata=payload["embedding_metadata"],
    pipeline=payload["pipeline"]
)

print("Final Embedding Content:")
print(json.dumps(final_embedding_content, indent=4, default=str))
print("\nFinal Embedding Metadata:")
print(json.dumps(final_embedding_metadata, indent=4, default=str))

# python -m src.embedding.modules.embedding_file