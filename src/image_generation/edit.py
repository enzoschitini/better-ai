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

from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class ImageManipulationService:
    DEFAULT_CONTENT_CONFIG = {
        "model": "gemini-2.5-flash-image",
        "temperature": 0.75,
        "top_p": 0.85,
        "max_output_tokens": 1024,
        "aspect_ratio": "1:1",
    }

    def __init__(self, client=None, content_config: Optional[Dict] = None):
        self.client = client or genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.content_config = self._build_content_config(content_config)

    def _build_content_config(self, content_config: Optional[Dict]) -> Dict:
        return {
            **self.DEFAULT_CONTENT_CONFIG,
            **(content_config or {})
        }

    def prints(self):
        print("\nContent Config:", self.content_config)
        print("\nClient:", self.client)

    def build_payload(self, prompt: str, images: Optional[List[Dict]] = None) -> Dict:
        if not prompt or not isinstance(prompt, str):
            raise ValueError("`prompt` é obrigatório e deve ser uma string não vazia.")

        return {
            "prompt": prompt,
            "content_config": self.content_config,
            "images": images or []
        }





    # 1. Build Parts (Prompt + Imagens)
    def build_parts(self, prompt: str, images: Optional[List[bytes]] = None) -> List[types.Part]:
        if not prompt or not isinstance(prompt, str):
            raise ValueError("`prompt` é obrigatório.")

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
            temperature=0.75,
            top_p=0.85,
            max_output_tokens=1024,
            response_modalities=["IMAGE", "TEXT"],
            image_config=types.ImageConfig(
                aspect_ratio="9:16"
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

        response = self.client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=contents,
            config=config
        )

        return response
    
    # 4. Response Parse (texto, imagens, metadata)
    def parse_response(self, response):
        # Base Response Structure
        text_response = None
        images = []

        if response.candidates:
            for part in response.candidates[0].content.parts:

                if part.text:
                    text_response = part.text

                if part.inline_data:
                    images.append({
                        "mime_type": part.inline_data.mime_type,
                        "data": part.inline_data.data  # bytes puros
                    })
        
        # Usage Metadata
        usage_metadata = None

        if response.usage_metadata:
            usage_metadata = {
                "prompt_tokens": response.usage_metadata.prompt_token_count,
                "output_tokens": response.usage_metadata.candidates_token_count,
                "total_tokens": response.usage_metadata.total_token_count
            }

        return {
            "text_response": text_response,
            "images": images,
            "usage_metadata": usage_metadata
        }











if __name__ == "__main__":
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

    editor = ImageManipulationService()
    parts = editor.build_parts(
        prompt="Gere uma imagem seguindo o estilo dessas",
        images=images
    )
    config = editor.generate_config()
    response = editor.call_model(parts, config)

    parsed = editor.parse_response(response)

    print(parsed["text_response"])
    print("Usage Metadata:", parsed["usage_metadata"])

    import os
    import uuid

    os.makedirs("img_test", exist_ok=True)

    for i, image in enumerate(parsed["images"]):
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






