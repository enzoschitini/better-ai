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

BUCKET_NAME = "images"
STORAGE_BASE_PATH = "image_generations"
ID_PREFIX = "img-"

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