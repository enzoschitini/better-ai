import os
from typing import List
from datetime import datetime

from src.image_generation.config import GeneratedImage
from src.storage.supabase.storage_menager import StorageManager

class StorageRepository:
    def __init__(self, base_path: str = None, bucket_name: str = None):
        self.base_path = base_path
        self.bucket_name = bucket_name
        os.makedirs(self.base_path, exist_ok=True)

    def local_repository(self, images: List[GeneratedImage], prefix: str = "image") -> List[str]:
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
    
    def upload_to_supabase(self, file_name: str, byte_data: bytes) -> str:
        manager = StorageManager(bucket_name=self.bucket_name)
        storage_name = f"{self.base_path}/{file_name}"

        upload_res = manager.upload_bytes(storage_name, byte_data)

        if upload_res:
            return manager.get_url(storage_name)
            



