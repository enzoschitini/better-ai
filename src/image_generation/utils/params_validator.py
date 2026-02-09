
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

class ImageParamsValidator:
    def __init__(self, catalog: dict | None = None):
        self.catalog = catalog or IMAGE_MODELS_CATALOG

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

