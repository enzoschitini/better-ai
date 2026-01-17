# https://github.com/enzoschitini/Asimov-Academy/tree/main/Google%20Ai/Nano%20Banana/doc
from google import genai
from PIL import Image
import os
from io import BytesIO

from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_images(
    prompt: str,
    *,
    model: str = "models/imagen-4.0-generate-001",
    number_of_images: int = 2,
    output_mime_type: str = "image/jpeg",
    aspect_ratio: str = "9:16",
    image_size: str = "2K",
) -> list[Image.Image]:
    """
    Gera imagens usando Gemini / Imagen e retorna uma lista de PIL Images.
    Não salva arquivos em disco.
    """

    result = client.models.generate_images(
        model=model,
        prompt=prompt,
        config=dict(
            number_of_images=number_of_images,
            output_mime_type=output_mime_type,
            aspect_ratio=aspect_ratio,
            image_size=image_size,
        ),
    )

    if not result.generated_images:
        return []

    images: list[Image.Image] = []

    for generated_image in result.generated_images:
        # `generated_image.image` já é um PIL.Image
        images.append(generated_image.image)

    return images


"""
| Modelo   | Resolução | Custo por imagem |
| -------- | --------- | ---------------- |
| imagen-4 | 1K        | ~$0.02           |
| imagen-4 | 2K        | ~$0.04           |
| imagen-4 | 4K        | ~$0.08           |
"""

def test():
    prompt = """
    An evocative image of an English afternoon tea table in a period drama setting,
    specifically reminiscent of the Queen Elizabeth I era. The table is adorned with
    a newspaper, prominently displaying the headline 'Gemini 2.5 in 2025'.
    Ensure the scene is rich in historical detail and atmosphere, but devoid of any
    human presence.
    """

    images = generate_images(prompt, number_of_images=2)

    for i, img in enumerate(images):
        img.save(f"generated_image_{i}.jpg")

test()
