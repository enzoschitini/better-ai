# class ImageEdit 
# (Request: Text/Image Byte/Image Byte List, Config Params) -> Response: Text, Image Byte List, Metadata

# 1. Build Parts (Prompt + Imagens)
# 2. Config (temperature, top_p, max_tokens, etc)
# 3. Model Call
# 4. Response Parse (texto, imagens, metadata)

import json
import magic # uv add python-magic-bin
import os

from google import genai
from google.genai import types

from src.image_generation.utils.config import DEFAULT_CONTENT_CONFIG
from src.image_generation.utils.gemini_client import GeminiClient

from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class ImageGeneratorService:
    def __init__(self, client=None, content_config: Optional[Dict] = None):
        self.client = client or GeminiClient().get_client()
        self.DEFAULT_CONTENT_CONFIG = DEFAULT_CONTENT_CONFIG
        self.content_config = self._build_content_config(content_config)

    def _build_content_config(self, content_config: Optional[Dict]) -> Dict:
        return {
            **self.DEFAULT_CONTENT_CONFIG,
            **(content_config or {})
        }

    # 1. Build Parts (Prompt + Imagens)
    def build_parts(self, prompt: str, instructions: Optional[str] = None, images: Optional[List[bytes]] = None) -> List[types.Part]:
        if not prompt or not isinstance(prompt, str):
            raise ValueError("`prompt` é obrigatório.")
        
        if instructions:
            prompt = f"""
            [ROLE]
            You are an AI specialized in image generation and editing.

            [TASK]
            {prompt}

            [USER_CONTEXT]
            {instructions or "N/A"}
            """

        parts = [
            types.Part.from_text(text=prompt)
        ]

        if images:
            mime = magic.Magic(mime=True)

            for image_bytes in images:
                mime_type = mime.from_buffer(image_bytes)

                parts.append(
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=mime_type
                    )
                )

        return parts
    
    # 2. Config (temperature, top_p, max_tokens, etc)
    def generate_config(self):
        config = types.GenerateContentConfig(
            temperature=self.content_config["temperature"],
            top_p=self.content_config["top_p"],
            max_output_tokens=self.content_config["max_output_tokens"],
            response_modalities=["IMAGE", "TEXT"],
            image_config=types.ImageConfig(
                aspect_ratio=self.content_config["aspect_ratio"]
            )
        )

        return config
    
    # 3. Model Call
    def call_model(self, parts: List[Dict], config: Dict):
        contents = [
            types.Content(
                role="user",
                parts=parts
            )
        ]

        responses = []

        for _ in range(self.content_config["number_of_images"]):
            response = self.client.models.generate_content(
                model=self.content_config["model"],
                contents=contents,
                config=config
            )
            responses.append(response)

        return responses

    
    # 4. Response Parse (múltiplos responses → text + imagens + metadados agregados)
    def parse_responses(self, responses):
        images = []
        usage_metadatas = []
        text_responses = []

        for response in responses:
            # Coleta imagens
            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        images.append({
                            "mime_type": part.inline_data.mime_type,
                            "data": part.inline_data.data  # bytes puros
                        })
                    elif part.text:
                        text_responses.append(part.text)

            # Coleta usage metadata por response
            if response.usage_metadata:
                usage_metadatas.append({
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "output_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count
                })
            else:
                usage_metadatas.append(None)

        return {
            "text_responses": text_responses,  # Lista de respostas textuais (pode ser útil para entender o contexto da geração)
            "images": images,  # Imagens de todos os responses
            "generate_config": self.content_config,  # content_config geral
            "usage_metadata": usage_metadatas  # Lista com o usage_metadata de cada response
        }



if __name__ == "__main__":

    import os
    import uuid

    # Load images

    base_image_paths = [
        "src/image_generation/backup/img1.jpeg",
        "src/image_generation/backup/img2.jpeg"
    ]

    images = []

    for path in base_image_paths:
        with open(path, "rb") as f:
            image_bytes = f.read()
        
        images.append(image_bytes)

    editor = ImageGeneratorService(content_config={"number_of_images": 2})
    
    parts = editor.build_parts(
        prompt="Gere uma imagem seguindo o estilo dessas",
        instructions="Crie uma imagem que combine elementos de ambas as imagens fornecidas, mantendo um estilo artístico coeso e atraente.",
        images=images
    )
    config = editor.generate_config()

    # Image Count
    response = editor.call_model(parts, config)

    responses_parsed = editor.parse_responses(response)

    print("Text Responses:", responses_parsed["text_responses"])
    print("Usage Metadata:", responses_parsed["usage_metadata"])
    print("Config:", responses_parsed["generate_config"])

    os.makedirs("img_test", exist_ok=True)

    for i, image in enumerate(responses_parsed["images"]):
        ext = image["mime_type"].split("/")[-1]  # png, jpeg, webp, etc
        filename = f"img_test/img_{i}_{uuid.uuid4().hex}.{ext}"

        with open(filename, "wb") as f:
            f.write(image["data"])

        print("Imagem salva em:", filename)




ImageEditPayload = {
    "prompt": "Gere uma imagem seguindo o estilo dessas",

    "content_config": {
        "model": "gemini-2.5-flash-image",
        "temperature": 0.75,
        "top_p": 0.85,
        "max_output_tokens": 1024,
        "aspect_ratio": "9:16"
    },

    "images": [
        {
            "bytes": b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00...\xff...",
            "mime_type": "image/jpeg"
        },
        {
            "bytes": b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00...\xff...",
            "mime_type": "image/jpeg"
        }
    ]
}

ImageEditResponse = {
    "text_response": "Claro, aqui está a imagem solicitada.",

    "images": [
        {
            "bytes": b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00...\xff...",
            "mime_type": "image/jpeg"
        }
    ],

    "usage_metadata": {
        "prompt_tokens": 100,
        "output_tokens": 100,
        "total_tokens": 200
    }
}


# python -m src.image_generation.edit






