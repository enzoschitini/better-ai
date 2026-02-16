from typing import List, Optional

from src.image_generation.utils.config import Imagen, GeneratedImage 
from src.image_generation.utils.params_validator import ImageParamsValidator
from dotenv import load_dotenv

load_dotenv()

class TextToImage:
    DEFAULT_MODEL = Imagen.GENERATE.id
    DEFAULT_NUMBER_OF_IMAGES = 1
    DEFAULT_OUTPUT_MIME_TYPE = "image/jpeg"
    DEFAULT_ASPECT_RATIO = Imagen.GENERATE.ratios.R1_1
    DEFAULT_IMAGE_SIZE = Imagen.GENERATE.resolutions.K1

    def __init__(self, client, validator: ImageParamsValidator):
        self.client = client
        self.validator = validator

    def _format_output(self, result) -> List[GeneratedImage]:
        """
        Formata a saída do provider para o DTO interno da aplicação.
        """
        if not result.generated_images:
            return []

        formatted: List[GeneratedImage] = []

        for img in result.generated_images:
            formatted.append(
                GeneratedImage(
                    image_bytes=img.image.image_bytes,
                    mime_type=img.image.mime_type,
                )
            )

        return formatted

    def generate(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        number_of_images: Optional[int] = None,
        output_mime_type: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        image_size: Optional[str] = None,
    ) -> List[GeneratedImage]:

        final_model = model or self.DEFAULT_MODEL
        final_number_of_images = number_of_images or self.DEFAULT_NUMBER_OF_IMAGES
        final_output_mime_type = output_mime_type or self.DEFAULT_OUTPUT_MIME_TYPE
        final_aspect_ratio = aspect_ratio or self.DEFAULT_ASPECT_RATIO
        final_image_size = image_size or self.DEFAULT_IMAGE_SIZE

        self.validator.validate(
            model=final_model,
            number_of_images=final_number_of_images,
            output_mime_type=final_output_mime_type,
            aspect_ratio=final_aspect_ratio,
            image_size=final_image_size,
        )

        result = self.client.models.generate_images(
            model=final_model,
            prompt=prompt,
            config=dict(
                number_of_images=final_number_of_images,
                output_mime_type=final_output_mime_type,
                aspect_ratio=final_aspect_ratio,
                image_size=final_image_size,
            ),
        )

        return self._format_output(result)


