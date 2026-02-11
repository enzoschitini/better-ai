# class ImageEdit 
# (Request: Text/Image Byte/Image Byte List, Config Params) -> Response: Text, Image Byte List, Metadata

# 1. Build Parts (Prompt + Imagens)
# 2. Config (temperature, top_p, max_tokens, etc)
# 3. Model Call
# 4. Response Parse (texto, imagens, metadata)

from src.image_generation.utils.gemini_client import GeminiClient

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

    def __init__(self, prompt: str, content_config: Optional[Dict] = None, images: Optional[List[Dict]] = None):
        self.prompt = prompt
        self.content_config = self._build_content_config(content_config)
        self.images = images or []

    def _build_content_config(self, content_config: Optional[Dict]) -> Dict:
        """
        Mergeia o config recebido com os defaults.
        Prioridade: valores passados pelo usuário > defaults
        """
        if not content_config:
            return self.DEFAULT_CONTENT_CONFIG.copy()

        return {
            **self.DEFAULT_CONTENT_CONFIG,
            **content_config
        }
    
    def prints(self):
        import json
        print("\n\nPrompt:", self.prompt)
        print("\nContent Config:", self.content_config)
        print("\nImages:", self.images, "\n\n")













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

    img = ImageEdit(
        prompt="Gere uma imagem...",
        content_config={
            "model": "gemini-2.5-flash-image",
            "temperature": 0.9,
            "top_p": 0.9,
            "max_output_tokens": 2048,
            "aspect_ratio": "9:16",
        },
        images=images
    )

    img.prints()





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






