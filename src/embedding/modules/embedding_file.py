import json

from io import BytesIO

from src.embedding.services.file_content_extractor import FileContentExtractor
from src.vector_store.pinecone.pinecone_vectorstore_services import PineconeVectorService

from src.tokens_calculate.token_counter import TokenCounter
from src.tokens_calculate.model_pricing import ModelPricingFactory
from src.tokens_calculate.exchange_rate.exchange_rate import ExchangeRateService

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
    
    def _calculate_cost(self, model: str, content: str) -> dict:
        pricing = ModelPricingFactory.create(model)
        counter = TokenCounter(model)

        tokens = counter.count(content)
        cost = pricing.cost(tokens)

        return {
            "caracter_count": len(content),
            "tokens": tokens,
            "cost_usd": f"{cost:.6f}"
        }

    def calculate_cost(self, model: str, final_embedding_content: dict) -> dict:
        exchange_service = ExchangeRateService()
        usd_rate = exchange_service.get_usd_rate()

        parts_cost_info = {}

        for key, value in final_embedding_content.items():
            parts_cost_info[key] = self._calculate_cost(model, value)

        total_caracter_count = sum(part["caracter_count"] for part in parts_cost_info.values())
        total_tokens = sum(part["tokens"] for part in parts_cost_info.values())
        total_cost_usd = f"{sum(float(part['cost_usd']) for part in parts_cost_info.values()):.6f}"

        usege_informations = {
            "total_caracter_count": total_caracter_count,
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost_usd,
            "exchange_rate": usd_rate
        }

        if len(parts_cost_info) > 1:
            usege_informations["parts"] = parts_cost_info

        print(json.dumps(usege_informations, indent=4))
        return usege_informations
    
    def save_to_vector_db(self, embedding_content: str, embedding_metadata: dict, flags: dict = None):
        # Aqui você implementaria a lógica para salvar os vetores de embedding e seus metadados em um banco de dados de vetores
        # Pode ser uma chamada para um serviço externo ou uma operação local, dependendo da sua arquitetura

        if flags:
            embedding_metadata = {**embedding_metadata, **flags}  # Adiciona as flags aos metadados
        
        pine_service = PineconeVectorService(
            embedding_model_name="text-embedding-3-large", 
            dimensions=3072
        )

        embed_response = pine_service.generate_vectors(
            text=embedding_content,
            metadata=embedding_metadata,
            save_global=False,
            batch_size=200
        )

        print(embed_response)
        return embed_response
        


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
            "model": "text-embedding-3-large",
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
file_content = embedder.extract_content(payload["file_info"]["extension"], payload["file_info"]["bytes"])

final_embedding_content, final_embedding_metadata = embedder.generate_embedding_payload(
    identifiers=payload["identifiers"],
    file_info=payload["file_info"],
    file_content=file_content[:100],
    embedding_metadata=payload["embedding_metadata"],
    pipeline=payload["pipeline"]
)

print("Final Embedding Content:")
print(json.dumps(final_embedding_content, indent=4, default=str))
print("\nFinal Embedding Metadata:")
print(json.dumps(final_embedding_metadata, indent=4, default=str))

usege_informations = embedder.calculate_cost(
    model=payload["embedding_settings"]["model"], 
    final_embedding_content=final_embedding_content
)

embed_response = embedder.save_to_vector_db(
    embedding_content=json.dumps(final_embedding_content),
    embedding_metadata=final_embedding_metadata,
    #flags={"group": "test_group"}
)

# python -m src.embedding.modules.embedding_file