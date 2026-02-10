import uuid
from src.image_generation.gemini_client import GeminiClient
from src.image_generation.config import Imagen

from src.image_generation.utils.params_validator import ImageParamsValidator
from src.image_generation.generation import ImageGenerator
from src.image_generation.utils.image_repository import ImageRepository

client = GeminiClient().get_client()
validator = ImageParamsValidator()
generator = ImageGenerator(client, validator)

prompts_examples = {
    "da_vinci_butterfly": """
Da Vinci style anatomical sketch of a dissected Monarch butterfly. Detailed drawings of the head, wings, and legs on textured parchment with notes in English.
""",

    "fantastic": """
Renaissance anatomical study of a mythical griffin, cross-sections of muscles and bones, vintage scientific notebook style.
""",

   "food": """
Create a vibrant infographic that explains photosynthesis as if it were a recipe for a plant's favorite food. Show the \"ingredients\" (sunlight, water, CO2) and the \"finished dish\" (sugar/energy). The style should be like a page from a colorful kids' cookbook, suitable for a 4th grader.
""",

   "ciclo_acqua": """
Create a comic-style infographic explaining the water cycle (evaporation, condensation, precipitation) with cute characters and simple explanations for children.
""",

   "ciclo_acqua": """
Create a comic-style infographic explaining the water cycle (evaporation, condensation, precipitation) with cute characters and simple explanations for children.
"""
}

images = generator.generate(
    prompt=prompts_examples["food"],
    model=Imagen.GENERATE.id,
    number_of_images=1,
    aspect_ratio=Imagen.GENERATE.ratios.R9_16,
    image_size=Imagen.GENERATE.resolutions.K2,
)

#response = repository.save_repository(images)
for img in images:
    unique_name = f"{uuid.uuid4().hex}.jpg"
    repository = ImageRepository(base_path=f"StorageManager/{unique_name}")

    file_url = repository.upload_to_supabase(bucket_name="images", byte_data=img.image_bytes)
    print(f"\n\nUploaded image URL: {file_url}\n")

# https://raw.githubusercontent.com/enzoschitini/better-ai/refs/heads/feature/SCRUM-78/storage/futuristic_city_20260204_113602_1.jpg?token=GHSAT0AAAAAADKHQUHFU522URHVHH2EFATC2MJ63FQ
# python -m src.image_generation.application

# Author: Enzo Schitini