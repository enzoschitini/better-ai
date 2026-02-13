from typing import Iterable, List, Union
from fastapi import UploadFile, HTTPException
from pathlib import Path

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"


class FilesPayloadBuilder:
    def __init__(
        self,
        max_mb: int = 10,
        max_files: int = 5,
        allowed_types: Iterable[str] = ("image/jpeg", "image/png"),
    ):
        self.max_bytes = max_mb * 1024 * 1024
        self.max_files = max_files
        self.allowed_types = set(allowed_types)

    async def build(self, files: Iterable[Union[UploadFile, bytes, Path]]) -> list[dict]:
        files = list(files)

        if not files:
            return []

        if len(files) > self.max_files:
            raise HTTPException(
                status_code=400,
                detail=f"Máximo de {self.max_files} arquivos permitidos."
            )

        payload = []

        for f in files:
            item = await self._normalize_file(f)
            self._validate_size(item)
            self._validate_type(item)

            payload.append(item)

        return payload

    async def _normalize_file(self, f: Union[UploadFile, bytes, Path]) -> dict:
        if isinstance(f, UploadFile):
            content = await f.read()
            return {
                "filename": f.filename,
                "content_type": f.content_type,
                "bytes": content,
                "size_bytes": len(content)
            }

        elif isinstance(f, Path):
            content = f.read_bytes()
            return {
                "filename": f.name,
                "content_type": None,
                "bytes": content,
                "size_bytes": len(content)
            }

        elif isinstance(f, bytes):
            return {
                "filename": "raw_bytes",
                "content_type": None,
                "bytes": f,
                "size_bytes": len(f)
            }

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de arquivo não suportado: {type(f)}"
            )

    def _validate_size(self, item: dict):
        if item["size_bytes"] > self.max_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo muito grande: {item['filename']} "
                       f"(máx {self.max_bytes // (1024 * 1024)}MB)"
            )

    def _validate_type(self, item: dict):
        content = item["bytes"]
        content_type = item.get("content_type")

        is_png = content.startswith(PNG_MAGIC)
        is_jpeg = content.startswith(JPEG_MAGIC)

        if not (is_png or is_jpeg):
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo inválido (não é PNG nem JPEG): {item['filename']}"
            )

        if content_type and content_type not in self.allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Formato não suportado: {content_type}. "
                       f"Aceitos: {', '.join(self.allowed_types)}"
            )




if __name__ == "__main__":
    """
    # FastAPI
    builder = FilesPayloadBuilder(max_mb=10, max_files=5)
    images_payload = await builder.build(files)

    # Bytes vindos de outro serviço
    builder = FilesPayloadBuilder()
    images_payload = await builder.build([
        {"filename": "a.png", "content_type": "image/png", "bytes": raw_bytes}
    ])

    # Caminhos de arquivo
    from pathlib import Path

    builder = FilesPayloadBuilder()
    images_payload = await builder.build([
        Path("/tmp/ref1.png"),
        Path("/tmp/ref2.jpg")
    ])

    # File-like (ex: BytesIO)
    from io import BytesIO

    buf = BytesIO(open("ref.png", "rb").read())

    builder = FilesPayloadBuilder()
    images_payload = await builder.build([buf])
    """

