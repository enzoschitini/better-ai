from src.image_generation.gemini_client import GeminiClient
from src.image_generation.config import GeneratedImage

from src.image_generation.utils.params_validator import ImageParamsValidator
from src.image_generation.generation import ImageGenerator
from src.image_generation.utils.image_repository import ImageRepository

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

client = GeminiClient().get_client()
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

# python -m src.image_generation.application