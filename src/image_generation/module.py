from src.image_generation.edit import ImageGeneratorService
from src.utils.unique_id_factory import IDGenerator

import os
import uuid

# Load images

def load_image_bytes():
    base_image_paths = [
        "src/image_generation/backup/img1.jpeg",
        "src/image_generation/backup/img2.jpeg"
    ]

    images = []

    for path in base_image_paths:
        with open(path, "rb") as f:
            image_bytes = f.read()
        
        images.append(image_bytes)
    
    return image_bytes

def gen(images):
    editor = ImageGeneratorService(content_config={"number_of_images": 2})

    parts = editor.build_parts(
        prompt="Gere uma imagem seguindo o estilo dessas",
        instructions="Crie uma imagem que combine elementos de ambas as imagens fornecidas, mantendo um estilo artístico coeso e atraente.",
        images=images
    )

    config = editor.generate_config()
    response = editor.call_model(parts, config)
    responses_parsed = editor.parse_responses(response)

    return responses_parsed

def save_results(responses_parsed):
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
    
    """
    Objetivo,Exemplo de Código,Exemplo de Retorno
    UUID v4 (Padrão),IDGenerator.uuid(),784a0d9b-2b41-4c12-8877-6f8d92305381
    Timestamp (Numérico),IDGenerator.timestamp(),17391845120004561
    Timestamp + Prefixo,"IDGenerator.timestamp(prefix=""USR"", separator=""_"")",USR_17391845120008219
    Timestamp (Hex/Curto),IDGenerator.timestamp(as_hex=True),18f74d0a2bc5f1a39
    Token Seguro (URL),IDGenerator.token(length=12),A9x_L2mNq4W1
    Máscara Customizada,"IDGenerator.custom(""TAG-####-??"")",TAG-4821-KM
    Serial Alfanumérico,"IDGenerator.custom(""****-****"")",A7j2-9PqL
    """

print(f"ID: {IDGenerator.timestamp(prefix="JOB-")}")

# python -m src.image_generation.module