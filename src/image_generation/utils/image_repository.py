import os
from typing import List
from datetime import datetime

from src.image_generation.config import GeneratedImage

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
