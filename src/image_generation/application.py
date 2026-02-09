import uuid
from src.image_generation.gemini_client import GeminiClient
from src.image_generation.config import GeneratedImage

from src.image_generation.utils.params_validator import ImageParamsValidator
from src.image_generation.generation import ImageGenerator
from src.image_generation.utils.image_repository import ImageRepository

client = GeminiClient().get_client()
validator = ImageParamsValidator()
generator = ImageGenerator(client, validator)

images = generator.generate(
    prompt="""
Da Vinci style anatomical sketch of a dissected Monarch butterfly. Detailed drawings of the head, wings, and legs on textured parchment with notes in English.
""",
    model="imagen-4.0-ultra-generate-001",
    number_of_images=3,
    aspect_ratio="9:16",
    image_size="2K",
)

#response = repository.save_repository(images)
for img in images:
    unique_name = f"{uuid.uuid4().hex}.jpg"
    repository = ImageRepository(base_path=f"StorageManager/{unique_name}")

    file_url = repository.upload_to_supabase(bucket_name="images", byte_data=img.image_bytes)
    print(f"Uploaded image URL: {file_url}")

# https://raw.githubusercontent.com/enzoschitini/better-ai/refs/heads/feature/SCRUM-78/storage/futuristic_city_20260204_113602_1.jpg?token=GHSAT0AAAAAADKHQUHFU522URHVHH2EFATC2MJ63FQ

# A cinematic photo of a futuristic city at night

# python -m src.image_generation.application