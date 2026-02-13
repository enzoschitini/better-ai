
from src.image_generation.calc import CostCalculator
from src.utils.unique_id_factory import IDGenerator
from src.image_generation.utils.config import ID_PREFIX, BASE_URL

class PayloadBuilder:
    def __init__(self):
        pass



    def _calculate_cost(self, usages_metadata: list):
        calculator = CostCalculator()
        usage_merged = calculator.merge_cost_information(usages_metadata)

        cost = calculator.calculate(
            model="gemini-3-pro-image-preview",
            prompt_tokens=usage_merged["prompt_tokens"],
            output_tokens=usage_merged["output_tokens"],
            total_tokens=usage_merged["total_tokens"],
            num_images=1,
        )

        return cost



    def payload_image_response(self, mime_types):
        image_response = []

        for mime_type in mime_types:
            dic = {
                "id": IDGenerator.timestamp(prefix=ID_PREFIX),
                "url": f"{BASE_URL}_{IDGenerator.timestamp(prefix=ID_PREFIX)}.{mime_type.split('/')[-1]}",
                "mime_type": mime_type,
                "byte": b"mdmdmdmdmd"
            }
            image_response.append(dic)

        
        return image_response
    
    def mongo_payload(self):
        payload = {
            "jobId": "1234567890",

            "user_input": {
                "prompt": "Gere uma imagem seguindo o estilo dessas",
                "instructions": "Crie uma imagem que combine elementos de ambas as imagens fornecidas, mantendo um estilo artístico coeso e atraente.",
                "images": 2
            },

            "text_response": "Claro, aqui está a imagem solicitada.",

            "image_response": self.payload_image_response(["image/jpeg"]),

            "generate_config": {
                "llm_model": "gemini-3-pro-image-preview",
                "temperature": 0.75,
                "top_p": 0.85,
                "max_output_tokens": 1024,
                "aspect_ratio": "1:1",
            },

            "cost_information": self._calculate_cost()
        }



"""
# Headers Informations
# Metadata
# Aggregates

{
    "model": "gemini-3-pro-image-preview",
    "pricing_version": "2026-02-11",
    "prompt_tokens": 526,
    "output_tokens": 12,
    "num_images": 1,
    "prompt_usd": 0.001052,
    "output_usd": 0.000144,
    "images_usd": 0.134,
    "cache_input_usd": 0.0,
    "cache_storage_usd": 0.0,
    "total_usd": 0.135196
}

mongo_payload = {
    "jobId": "1234567890",

    "text_input": {
        "user_input": "Gere uma imagem seguindo o estilo dessas",
        "instructions": "Crie uma imagem que combine elementos de ambas as imagens fornecidas, mantendo um estilo artístico coeso e atraente.",
        "images": 2
    },

    "text_response": "Claro, aqui está a imagem solicitada.",

    "image_response": [
        {
            "id": "response_id_1",
            "url": "https://example.com/generated_image_1.jpg",
            "mime_type": "image/jpeg"
        }
    ],

    "generate_config": {
        "llm_model": "gemini-3-pro-image-preview",
        "temperature": 0.75,
        "top_p": 0.85,
        "max_output_tokens": 1024,
        "aspect_ratio": "1:1",
    },

    "cost_information": {
        "prompt_tokens": 526,
        "output_tokens": 12,
        "prompt_usd": 0.001052,
        "output_usd": 0.000144,
        "images_usd": 0.134,
        "total_usd": 0.135196
    }
}

response_payload = {
    "jobId": "1234567890",
    "text_response": "Claro, aqui está a imagem solicitada.",
    "images": [
        "https://example.com/generated_image_1.jpg",
        "https://example.com/generated_image_2.jpg"
    ]
}
"""
