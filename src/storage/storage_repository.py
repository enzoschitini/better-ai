import os
from typing import List
from datetime import datetime

from src.image_generation.utils.config import GeneratedImage
from src.database.supabase_integration import BytesSource, UploadOptions
from src.database.supabase_integration.errors import SupabaseIntegrationError
from src.database.supabase_provider import get_supabase

class StorageRepository:
    def __init__(self, base_path: str = None, bucket_name: str = None):
        self.base_path = base_path
        self.bucket_name = bucket_name

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
        """Envia os bytes para ``<base_path>/<file_name>`` no bucket e devolve a URL pública.

        O tipo do arquivo é inferido da extensão e do conteúdo (a integração valida a coerência).
        O bucket precisa estar em ``SBX_BUCKETS_PUBLIC`` para gerar URL pública.
        """
        storage_name = f"{self.base_path}/{file_name}"
        storage = get_supabase().storage

        try:
            stored = storage.upload(
                BytesSource(byte_data, filename=file_name),
                UploadOptions(bucket=self.bucket_name, path=storage_name),
            )
            return storage.public_url(stored.path, bucket=stored.bucket)
        except SupabaseIntegrationError as exc:
            raise RuntimeError(f"Falha ao fazer upload para o Supabase: {storage_name}") from exc

if __name__ == "__main__":
    # Exemplo de uso
    repository = StorageRepository(base_path="images/image_generations", bucket_name="images")
    
    # Carregar bytes de imagem
    with open("src/storage/image.png", "rb") as f:
        image_bytes = f.read()

    # Salvar
    url = repository.upload_to_supabase(file_name="example_image.jpg", byte_data=image_bytes)
    print(f"Imagem salva no Supabase com URL: {url}")

    # python -m src.storage.storage_repository

