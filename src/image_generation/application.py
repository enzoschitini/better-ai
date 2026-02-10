from src.image_generation.gemini_client import GeminiClient
from src.image_generation.config import Imagen, BUCKET_NAME, STORAGE_BASE_PATH, ID_PREFIX

from src.image_generation.utils.params_validator import ImageParamsValidator
from src.image_generation.generation import ImageGenerator
from src.storage.storage_repository import StorageRepository
from src.image_generation.utils.unique_id_factory import IDGenerator

client = GeminiClient().get_client()
validator = ImageParamsValidator()
generator = ImageGenerator(client, validator)
repository = StorageRepository(base_path=STORAGE_BASE_PATH, bucket_name=BUCKET_NAME)


images = generator.generate(
    prompt="""
Da Vinci style anatomical sketch of a dissected Monarch butterfly. Detailed drawings of the head, wings, and legs on textured parchment with notes in English.
""",
    model=Imagen.GENERATE.id,
    number_of_images=1,
    aspect_ratio=Imagen.GENERATE.ratios.R16_9,
    image_size=Imagen.GENERATE.resolutions.K2,
)

for img in images:
    id = IDGenerator.timestamp(prefix=ID_PREFIX)
    extension = img.mime_type.split('/')[-1]

    unique_name = f"{id}.{extension}"
    file_url = repository.upload_to_supabase(file_name=unique_name, byte_data=img.image_bytes)

    print(f"\n\nUploaded image URL: {file_url}\n")







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

# https://hsenyunovbrmjejxqvjn.supabase.co/storage/v1/object/public/images/StorageManager/53fcbab5931945a0a5965936fb8ddc58.jpg
# python -m src.image_generation.application
# StorageManager

# Author: Enzo Schitini