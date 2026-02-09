from src.image_generation.gemini_client import GeminiClient
from src.image_generation.config import GeneratedImage

from src.image_generation.utils.params_validator import ImageParamsValidator
from src.image_generation.generation import ImageGenerator
from src.image_generation.utils.image_repository import ImageRepository

client = GeminiClient().get_client()
validator = ImageParamsValidator()
generator = ImageGenerator(client, validator)
repository = ImageRepository(base_path="storage")

images = generator.generate(
    prompt="""
Da Vinci style anatomical sketch of a dissected Monarch butterfly. Detailed drawings of the head, wings, and legs on textured parchment with notes in English.
""",
    model="imagen-4.0-ultra-generate-001",
    number_of_images=1,
    aspect_ratio="9:16",
    image_size="2K",
)

paths = repository.save_repository(images)

print(paths)

# https://raw.githubusercontent.com/enzoschitini/better-ai/refs/heads/feature/SCRUM-78/storage/futuristic_city_20260204_113602_1.jpg?token=GHSAT0AAAAAADKHQUHFU522URHVHH2EFATC2MJ63FQ

# A cinematic photo of a futuristic city at night

# python -m src.image_generation.application