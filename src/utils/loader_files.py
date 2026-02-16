from typing import List, Iterable
from fastapi import UploadFile, HTTPException

class FilesPayloadBuilder:
    def __init__(self, max_mb: int = 10, allowed_types: Iterable[str] = ("image/jpeg", "image/png")):
        self.max_bytes = max_mb * 1024 * 1024
        self.allowed_types = set(allowed_types)

    async def build_images_payload(self, files: List[UploadFile]) -> list[dict]:
        """
        Valida e transforma UploadFile em payload estruturado.

        :param files: Lista de arquivos enviados via multipart/form-data
        :type files: List[UploadFile]

        :return: Lista de dicionários com bytes e metadados
        :rtype: list[dict]
        """

        payload: list[dict] = []

        for f in files:
            content = await f.read()

            # ✅ Validação de tipo (header HTTP)
            if f.content_type not in self.allowed_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Formato não suportado: {f.content_type}. Aceitos: {', '.join(self.allowed_types)}."
                )

            # ✅ Validação de tamanho
            if len(content) > self.max_bytes:
                raise HTTPException(
                    status_code=400,
                    detail=f"Arquivo muito grande: {f.filename}. Máx: {self.max_bytes // (1024 * 1024)}MB."
                )

            payload.append({
                "filename": f.filename,
                "content_type": f.content_type,
                "size_bytes": len(content),
                "bytes": content,
            })

        return payload