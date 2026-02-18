import os
import uuid

from src.image_generation.image_generator_service import ImageGeneratorService

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

    editor = ImageGeneratorService(
        content_config={
            #"model": "gemini-2.5-flash-image",
            "model": "gemini-3-pro-image-preview",
            "temperature": 0.75,
            "top_p": 0.85,
            "max_output_tokens": 1024,
            "aspect_ratio": "9:16"
        }
    )

    # MAX TOKENS:
    # gemini-2.5-flash-image - 1024, 2048
    # gemini-3-pro-image-preview - 4096, 8192
    
    parts = editor.build_parts(
        user_prompt="Gere uma imagem seguindo o estilo dessas",
        instructions="Crie uma imagem que combine elementos de ambas as imagens fornecidas, mantendo um estilo artístico coeso e atraente.",
        images=images
    )
    
    config = editor.generate_config()
    response = editor.call_model(parts, config)
    responses_parsed = editor.parse_responses(response)

    print("Text Input:", responses_parsed["text_input"])
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
    "instructions": "....",

    "content_config": {
        "model": "gemini-2.5-flash-image",
        "temperature": 0.75,
        "top_p": 0.85,
        "max_output_tokens": 1024,
        "aspect_ratio": "9:16"
    },

    "images": [b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00...\xff...", b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00...\xff..."]
}

ImageEditResponse = {
    "text_responses": ['Com certeza! Aqui está uma imagem que combina elementos das duas imagens fornecidas, mantendo um estilo artístico coeso e atraente: ', 'Com certeza! Que tal uma imagem que combine a majestade do grifo com a delicadeza e os detalhes anatômicos da borboleta, tudo no mesmo estilo de ilustração? Aqui está: '],

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
    ],

    "usage_metadata": [
         {'prompt_tokens': 587, 'output_tokens': 1320, 'total_tokens': 1907}, 
         {'prompt_tokens': 587, 'output_tokens': 1313, 'total_tokens': 1900}
    ]
}


# python -m src.image_generation.test.ImageGeneratorService