from src.image_generation.calc import CostCalculator
from src.utils.unique_id_factory import IDGenerator
from src.image_generation.utils.config import ID_PREFIX, BASE_URL, DEFAULT_CONTENT_CONFIG

from typing import List, Dict, Optional, Tuple
import json
import copy
class PayloadBuilder:
    def __init__(self, job_id: str, dic: Dict):
        self.job_id = job_id
        self._raw = dic

        self.text_input: Dict = dic.get("text_input", {})
        self.text_responses: List[str] = dic.get("text_responses", [])
        self.images: List[Dict] = dic.get("images", [])
        self.generate_config: Dict = dic.get("generate_config", DEFAULT_CONTENT_CONFIG)
        self.usage_metadata: List[Dict] = dic.get("usage_metadata", [])

        self._cached_cost = None

    def _calculate_cost(self) -> Dict:
        if self._cached_cost:
            return self._cached_cost

        calculator = CostCalculator()
        usage_merged = calculator.merge_cost_information(self.usage_metadata)

        cost = calculator.calculate(
            model=self.generate_config["model"],
            prompt_tokens=usage_merged.get("prompt_tokens", 0),
            output_tokens=usage_merged.get("output_tokens", 0),
            total_tokens=usage_merged.get("total_tokens", 0),
            num_images=self.generate_config.get("number_of_images", 0),
        )

        self._cached_cost = cost
        return cost

    def _payload_image_response(self) -> Tuple[List[Dict], List[Dict], List[str]]:
        image_response = []
        image_bytes = []
        urls = []

        for img in self.images:
            mime_type = img.get("mime_type")
            data = img.get("data")

            if not mime_type or not data:
                continue

            file_id = IDGenerator.timestamp(prefix=ID_PREFIX)
            ext = mime_type.split("/")[-1]
            url = f"{BASE_URL}_{file_id}.{ext}"

            public_dict = {
                "id": file_id,
                "url": url,
                "mime_type": mime_type
            }

            internal_dict = {
                **public_dict,
                "byte": data
            }

            image_response.append(public_dict)
            image_bytes.append(internal_dict)
            urls.append(url)

        return image_response, image_bytes, urls

    def _build_base_payload(self) -> Dict:
        image_response, image_bytes, urls = self._payload_image_response()

        payload = {
            "jobId": self.job_id,
            "user_input": self.text_input,
            "text_response": self.text_responses[0] if self.text_responses else None,
            "image_response": image_response,
            "images_storage": image_bytes,
            "generate_config": self.generate_config,
            "cost_information": self._calculate_cost()
        }

        return payload, urls

    def generate_payloads(self):
        payload, urls = self._build_base_payload()

        mongo_payload = copy.deepcopy(payload)
        mongo_payload.pop("images_storage", None)

        storage_payload = payload["images_storage"]

        response_payload = {
            "jobId": payload["jobId"],
            "text_response": payload["text_response"],
            "images": urls
        }

        return mongo_payload, storage_payload, response_payload

if __name__ == "__main__":

    dic = {
        "text_input": {
            "user_prompt": "Gere uma imagem seguindo o estilo dessas",
            "instructions": "xxxxxxxxxxxxx",
            "images_count": 0
        },
        "text_responses": ['Com certeza! Aqui está uma imagem que combina elementos das duas imagens fornecidas, mantendo um estilo artístico coeso e atraente: ', 'Com certeza! Que tal uma imagem que combine a majestade do grifo com a delicadeza e os detalhes anatômicos da borboleta, tudo no mesmo estilo de ilustração? Aqui está: '],  # Lista de respostas textuais (pode ser útil para entender o contexto da geração)
        "images": [{"mime_type": "image/png", "data": "xxxxxxxxxxxxxxx"}, {"mime_type": "image/png", "data": "xxxxxxxxxxxxxxx"}],
        "generate_config": DEFAULT_CONTENT_CONFIG,
        "usage_metadata": [{'prompt_tokens': 587, 'output_tokens': 1320, 'total_tokens': 1907}, {'prompt_tokens': 587, 'output_tokens': 1313, 'total_tokens': 1900}]
    }

    payload_builder = PayloadBuilder(IDGenerator.timestamp(prefix="job_"), dic)
    mongo_payload, storage_payload, response_payload = payload_builder.generate_payloads()

    print(f"\n\nmongo_payload: {json.dumps(mongo_payload, indent=4)}")
    print(f"\n\nstorage_payload: {json.dumps(storage_payload, indent=4)}")
    print(f"\n\nresponse_payload: {json.dumps(response_payload, indent=4)}")
    
    # python -m src.image_generation.payload_builder


































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
