from typing import List, Optional
from PIL import Image

class ImageGenerator:
    """
    Classe responsável por gerar imagens usando Gemini / Imagen.
    Não salva arquivos em disco.
    """

    DEFAULT_MODEL = "models/imagen-4.0-generate-001"
    DEFAULT_NUMBER_OF_IMAGES = 2
    DEFAULT_OUTPUT_MIME_TYPE = "image/jpeg"
    DEFAULT_ASPECT_RATIO = "9:16"
    DEFAULT_IMAGE_SIZE = "2K"

    def __init__(self, client):
        self.client = client

    def generate(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        number_of_images: Optional[int] = None,
        output_mime_type: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        image_size: Optional[str] = None,
    ) -> List[Image.Image]:
        """
        Gera imagens usando Gemini / Imagen e retorna uma lista de PIL Images.
        Não salva arquivos em disco.
        """

        result = self.client.models.generate_images(
            model=model or self.DEFAULT_MODEL,
            prompt=prompt,
            config=dict(
                number_of_images=number_of_images or self.DEFAULT_NUMBER_OF_IMAGES,
                output_mime_type=output_mime_type or self.DEFAULT_OUTPUT_MIME_TYPE,
                aspect_ratio=aspect_ratio or self.DEFAULT_ASPECT_RATIO,
                image_size=image_size or self.DEFAULT_IMAGE_SIZE,
            ),
        )

        if not result.generated_images:
            return []

        images: List[Image.Image] = []

        for generated_image in result.generated_images:
            images.append(generated_image.image)

        return images
