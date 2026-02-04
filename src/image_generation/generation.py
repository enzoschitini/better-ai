# =========================
# CATALOG
# =========================

IMAGE_MODELS_CATALOG = {
    "imagen-4.0-generate-001": {
        "max_output_images_per_prompt": 4,
        "supported_aspect_ratios": ["1:1", "3:4", "4:3", "9:16", "16:9"],
        "supported_resolutions": ["1K", "2K"],
        "mime_types": ["image/png", "image/jpeg"],
    },
    "imagen-4.0-fast-generate-001": {
        "max_output_images_per_prompt": 4,
        "supported_aspect_ratios": ["1:1", "3:4", "4:3", "9:16", "16:9"],
        "supported_resolutions": ["1K"],
        "mime_types": ["image/png", "image/jpeg"],
    },
    "imagen-4.0-ultra-generate-001": {
        "max_output_images_per_prompt": 4,
        "supported_aspect_ratios": ["1:1", "3:4", "4:3", "9:16", "16:9"],
        "supported_resolutions": ["1K", "2K"],
        "mime_types": ["image/png", "image/jpeg"],
    },
}

# =========================
# IMPORTS
# =========================

import os
from io import BytesIO
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

from dotenv import load_dotenv
from google import genai
from PIL import Image

# =========================
# ENV
# =========================

load_dotenv()

# =========================
# Classe de Validação
# =========================
@dataclass
class GeminiConfig:
    api_key_env: str = "GEMINI_API_KEY"

    def get_api_key(self) -> str:
        api_key = os.getenv(self.api_key_env)

        if not api_key:
            raise EnvironmentError(
                f"Variável de ambiente '{self.api_key_env}' não encontrada."
            )

        return api_key


# =========================
# Classe de Client
# =========================
@dataclass
class GeminiClient:
    config: GeminiConfig
    _client: Optional[genai.Client] = None

    def get_client(self) -> genai.Client:
        if self._client is None:
            api_key = self.config.get_api_key()
            self._client = genai.Client(api_key=api_key)

        return self._client


# =========================
# DTO
# =========================

@dataclass
class GeneratedImage:
    image_bytes: bytes
    mime_type: str

# =========================
# VALIDATOR
# =========================

class ImageParamsValidator:
    def __init__(self, catalog: dict):
        self.catalog = catalog

    def validate(
        self,
        *,
        model: str,
        number_of_images: int,
        output_mime_type: str,
        aspect_ratio: str,
        image_size: str,
    ) -> None:
        # valida modelo
        if model not in self.catalog:
            raise ValueError(f"Invalid model: '{model}'")

        specs = self.catalog[model]

        # valida quantidade de imagens
        if number_of_images < 1:
            raise ValueError("number_of_images must be >= 1")

        if number_of_images > specs["max_output_images_per_prompt"]:
            raise ValueError(
                f"number_of_images={number_of_images} exceeds maximum allowed "
                f"({specs['max_output_images_per_prompt']}) for model {model}"
            )

        # valida mime type
        if output_mime_type not in specs["mime_types"]:
            raise ValueError(
                f"output_mime_type '{output_mime_type}' is not supported for {model}. "
                f"Supported: {specs['mime_types']}"
            )

        # valida aspect ratio
        if aspect_ratio not in specs["supported_aspect_ratios"]:
            raise ValueError(
                f"aspect_ratio '{aspect_ratio}' is not supported for {model}. "
                f"Supported: {specs['supported_aspect_ratios']}"
            )

        # valida resolução (1K, 2K, etc)
        if image_size not in specs["supported_resolutions"]:
            raise ValueError(
                f"image_size '{image_size}' is not supported for {model}. "
                f"Supported: {specs['supported_resolutions']}"
            )

# =========================
# GENERATOR
# =========================

class ImageGenerator:
    DEFAULT_MODEL = "imagen-4.0-generate-001"
    DEFAULT_NUMBER_OF_IMAGES = 1
    DEFAULT_OUTPUT_MIME_TYPE = "image/jpeg"
    DEFAULT_ASPECT_RATIO = "1:1"
    DEFAULT_IMAGE_SIZE = "1K"

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

# =========================
# REPOSITORY (PERSISTENCE)
# =========================

class ImageRepository:
    def __init__(self, base_path: str = "generated_images"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def save_repository(self, images: List[GeneratedImage], prefix: str = "image") -> List[str]:
        """
        Salva imagens localmente e retorna os caminhos salvos.
        """
        saved_paths: List[str] = []
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        for index, img in enumerate(images, start=1):
            extension = self._mime_to_extension(img.mime_type)
            filename = f"{prefix}_{timestamp}_{index}.{extension}"
            file_path = os.path.join(self.base_path, filename)

            with open(file_path, "wb") as f:
                f.write(img.image_bytes)

            saved_paths.append(file_path)

        return saved_paths

    def _mime_to_extension(self, mime_type: str) -> str:
        if mime_type == "image/jpeg":
            return "jpg"
        if mime_type == "image/png":
            return "png"
        raise ValueError(f"Unsupported mime type for persistence: {mime_type}")

# =========================
# USAGE EXAMPLE
# =========================

client_manager = GeminiClient()
client = client_manager.get_client()

validator = ImageParamsValidator(IMAGE_MODELS_CATALOG)
generator = ImageGenerator(client, validator)
repository = ImageRepository(base_path="storage/images")

images = generator.generate(
    prompt="""
Da Vinci style anatomical sketch of a dissected Monarch butterfly. Detailed drawings of the head, wings, and legs on textured parchment with notes in English.
""",
    model="imagen-4.0-ultra-generate-001",
    number_of_images=1,
    aspect_ratio="9:16",
    image_size="2K",
)

paths = repository.save_repository(images, prefix="mappa")

print(paths)

# A cinematic photo of a futuristic city at night
