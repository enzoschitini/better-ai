# class ImageEdit 
# (Request: Text/Image Byte/Image Byte List, Config Params) -> Response: Text, Image Byte List, Metadata

# 1. Build Parts (Prompt + Imagens)
# 2. Config (temperature, top_p, max_tokens, etc)
# 3. Model Call
# 4. Response Parse (texto, imagens, metadata)

import json
from src.image_generation.utils.gemini_client import GeminiClient

from google.genai import types

client = GeminiClient().get_client()


from typing import List, Dict, Optional


class ImageEdit:
    DEFAULT_CONTENT_CONFIG = {
        "model": "gemini-2.5-flash-image",
        "temperature": 0.75,
        "top_p": 0.85,
        "max_output_tokens": 1024,
        "aspect_ratio": "1:1",
    }

    def __init__(self, content_config: Optional[Dict] = None):
        self.content_config = self._build_content_config(content_config)

    def _build_content_config(self, content_config: Optional[Dict]) -> Dict:
        return {
            **self.DEFAULT_CONTENT_CONFIG,
            **(content_config or {})
        }

    def prints(self):
        print("\nContent Config:", self.content_config)

    def build_payload(self, prompt: str, images: Optional[List[Dict]] = None) -> Dict:
        if not prompt or not isinstance(prompt, str):
            raise ValueError("`prompt` é obrigatório e deve ser uma string não vazia.")

        return {
            "prompt": prompt,
            "content_config": self.content_config,
            "images": images or []
        }
    
    # 1. Build Parts (Prompt + Imagens)
    def build_parts(self, prompt: str, images: Optional[List[Dict]] = None) -> List[Dict]:
        # Prompt

        parts = [
            types.Part.from_text(
                text="Gere uma imagem seguindo o estilo dessas"
            )
        ]

        # Imagens Base (opcional)
        mime = magic.Magic(mime=True)

        for image_bytes in images:
            mime_type = mime.from_buffer(image_bytes)

            parts.append(
                types.Part.from_bytes(
                    data=image_bytes[:100],
                    mime_type=mime_type
                )
            )
        
        print("\nParts:", parts)

        return parts












if __name__ == "__main__":
    # Load images

    import magic # uv add python-magic-bin

    base_image_paths = [
        "src/image_generation/backup/img1.jpeg",
        "src/image_generation/backup/img2.jpeg"
    ]

    #mime = magic.Magic(mime=True)

    images = []

    for path in base_image_paths:
        with open(path, "rb") as f:
            image_bytes = f.read()
        
        images.append(image_bytes[:100])
        
        """
        mime_type = mime.from_buffer(image_bytes)

        images.append({
            "bytes": image_bytes[:100],
            "mime_type": mime_type
        })
        """

    print(images)

    editor = ImageEdit(
        content_config={
            "temperature": 0.9,
            "aspect_ratio": "9:16"
        }
    )

    payload = editor.build_payload(
        prompt="Gere uma imagem no estilo dessas",
        images=images  # opcional
    )

    print(payload)

    editor.build_parts(
        prompt="Gere uma imagem no estilo dessas",
        images=images
    )





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






