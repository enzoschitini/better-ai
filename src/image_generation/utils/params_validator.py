from src.image_generation.utils.config import IMAGE_MODELS_CATALOG
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


# python -m src.image_generation.utils.params_validator