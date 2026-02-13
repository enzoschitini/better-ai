from dataclasses import dataclass

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

# Storage
BUCKET_NAME = "images"
STORAGE_BASE_PATH = "image_generations"
ID_PREFIX = "img_"
BASE_URL = "https://example.com/generated_image"

# MongoDB
DATABASE_NAME = "DB_TEST_CLASS"
COLLECTION_NAME = "COL_TEST_CLASS"

DEFAULT_CONTENT_CONFIG = {
    "model": "gemini-2.5-flash-image",
    "temperature": 0.75,
    "top_p": 0.85,
    "max_output_tokens": 1024,
    "aspect_ratio": "1:1",
    "number_of_images": 1
}

BASE_PROMPT = """
[ROLE]
You are a multimodal AI agent specialized in visual creation and transformation.
You can generate new images from text, edit existing images, and create visual variations.
You understand composition, lighting, color theory, perspective, realism, illustration styles,
and can infer visual styles, patterns, and aesthetics from reference images provided by the user.

Your goals:
- Faithfully follow the user request.
- When reference images are provided, extract and apply relevant visual styles, aesthetics, composition patterns,
  color palettes, and artistic direction to the generated output.
- Preserve important visual constraints from the user instructions.
- When editing images, modify only what is explicitly requested and preserve the rest.
- When instructions are ambiguous, infer the most reasonable interpretation and produce a high-quality result.

Constraints:
- Do not add elements that were not requested.
- Do not remove important elements unless explicitly instructed.
- Avoid unnecessary alterations when performing edits.
- Prioritize visual consistency, coherence, and high-quality output.
"""

@dataclass
class GeneratedImage:
    image_bytes: bytes
    mime_type: str

@dataclass(frozen=True)
class Ratios:
    R1_1: str = "1:1"
    R3_4: str = "3:4"
    R4_3: str = "4:3"
    R9_16: str = "9:16"
    R16_9: str = "16:9"

@dataclass(frozen=True)
class Resolutions:
    K1: str = "1K"
    K2: str = "2K"

@dataclass(frozen=True)
class MimeTypes:
    PNG: str = "image/png"
    JPEG: str = "image/jpeg"

@dataclass(frozen=True)
class ModelSpecs:
    id: str
    max_images: int
    ratios: Ratios
    resolutions: Resolutions
    mimes: MimeTypes

class Imagen:
    GENERATE = ModelSpecs(
        id="imagen-4.0-generate-001",
        max_images=4,
        ratios=Ratios(),
        resolutions=Resolutions(),
        mimes=MimeTypes()
    )
    
    FAST = ModelSpecs(
        id="imagen-4.0-fast-generate-001",
        max_images=4,
        ratios=Ratios(),
        resolutions=Resolutions(K2=None),
        mimes=MimeTypes()
    )

    ULTRA = ModelSpecs(
        id="imagen-4.0-ultra-generate-001",
        max_images=4,
        ratios=Ratios(),
        resolutions=Resolutions(),
        mimes=MimeTypes()
    )


IMAGE_INTRO_SENTENCES = [
    "Aqui está a imagem conforme solicitado.",
    "Segue a imagem de acordo com o seu pedido.",
    "A imagem solicitada está pronta.",
    "Aqui está a imagem gerada para você.",
    "Preparei a imagem conforme você pediu.",
    "Segue a imagem resultante do seu pedido.",
    "Aqui está a imagem final.",
    "A imagem solicitada foi preparada.",
    "Segue a imagem conforme sua solicitação.",
    "Aqui está a imagem produzida para você.",
    "Preparei a imagem solicitada.",
    "A imagem resultante do seu pedido está pronta.",
    "Aqui está a imagem conforme seu pedido.",
    "Segue a imagem gerada conforme solicitado.",
    "A imagem final está pronta.",
    "Preparei a imagem de acordo com sua solicitação.",
    "Aqui está a imagem criada para você.",
    "Segue a imagem preparada conforme seu pedido.",
    "A imagem solicitada está disponível.",
    "Aqui está a imagem produzida conforme solicitado.",
    "Preparei a imagem final conforme seu pedido.",
    "Segue a imagem gerada para você.",
    "Aqui está a imagem conforme sua solicitação.",
    "A imagem resultante foi preparada.",
    "Segue a imagem criada conforme pedido.",
    "Aqui está a imagem pronta para você.",
    "Preparei a imagem resultante conforme solicitado.",
    "A imagem foi preparada conforme seu pedido.",
    "Segue a imagem final conforme solicitado.",
    "Aqui está a imagem criada conforme sua solicitação.",
    "A imagem solicitada foi criada para você.",
    "Preparei a imagem conforme seu pedido.",
    "Aqui está a imagem resultante conforme solicitado.",
    "Segue a imagem preparada para você.",
    "A imagem criada conforme seu pedido está pronta.",
    "Aqui está a imagem solicitada conforme pedido.",
    "Preparei a imagem conforme solicitado.",
    "Segue a imagem criada para você.",
    "A imagem final conforme seu pedido está pronta.",
    "Aqui está a imagem gerada conforme sua solicitação.",
    "Preparei a imagem final para você.",
    "Segue a imagem conforme pedido.",
    "A imagem produzida conforme solicitado está pronta.",
    "Aqui está a imagem criada conforme pedido.",
    "Preparei a imagem gerada para você.",
    "Segue a imagem conforme sua solicitação.",
    "A imagem final solicitada está pronta.",
    "Aqui está a imagem preparada conforme seu pedido.",
    "Preparei a imagem criada conforme solicitado.",
    "Segue a imagem pronta conforme pedido.",
]
