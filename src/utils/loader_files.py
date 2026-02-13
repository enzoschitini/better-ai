from typing import Iterable, List, TypedDict, BinaryIO, Union
from pathlib import Path
from fastapi import UploadFile, HTTPException
import mimetypes

class FilePayload(TypedDict):
    filename: str
    content_type: str
    size_bytes: int
    bytes: bytes

class FilesPayloadBuilder:
    def __init__(
        self,
        max_mb: int = 10,
        allowed_types: Iterable[str] = ("image/jpeg", "image/png"),
        max_files: int | None = None
    ):
        self.max_bytes = max_mb * 1024 * 1024
        self.allowed_types = set(allowed_types)
        self.max_files = max_files

    # --------- Validadores internos ---------

    def _is_png(self, data: bytes) -> bool:
        return data.startswith(b"\x89PNG\r\n\x1a\n")

    def _is_jpeg(self, data: bytes) -> bool:
        return data.startswith(b"\xff\xd8")

    def _validate_bytes(self, filename: str, content_type: str, data: bytes) -> None:
        if content_type not in self.allowed_types:
            raise HTTPException(400, f"Formato não suportado: {content_type}")

        if len(data) > self.max_bytes:
            raise HTTPException(400, f"Arquivo muito grande: {filename}")

        if content_type == "image/png" and not self._is_png(data):
            raise HTTPException(400, f"Arquivo inválido (PNG header): {filename}")

        if content_type == "image/jpeg" and not self._is_jpeg(data):
            raise HTTPException(400, f"Arquivo inválido (JPEG header): {filename}")

    # --------- Normalizadores por tipo de entrada ---------

    async def _from_upload_file(self, f: UploadFile) -> FilePayload:
        data = await f.read()
        return self._build_payload(f.filename, f.content_type or "application/octet-stream", data)

    def _from_bytes(self, data: bytes, filename: str = "file.bin", content_type: str = "application/octet-stream") -> FilePayload:
        return self._build_payload(filename, content_type, data)

    def _from_path(self, path: Path) -> FilePayload:
        data = path.read_bytes()
        content_type, _ = mimetypes.guess_type(str(path))
        return self._build_payload(path.name, content_type or "application/octet-stream", data)

    def _from_file_like(self, file_obj: BinaryIO, filename: str = "file.bin", content_type: str = "application/octet-stream") -> FilePayload:
        data = file_obj.read()
        return self._build_payload(filename, content_type, data)

    def _from_payload(self, payload: dict) -> FilePayload:
        return self._build_payload(
            payload["filename"],
            payload["content_type"],
            payload["bytes"]
        )

    # --------- Builder central ---------

    def _build_payload(self, filename: str, content_type: str, data: bytes) -> FilePayload:
        self._validate_bytes(filename, content_type, data)

        return {
            "filename": filename,
            "content_type": content_type,
            "size_bytes": len(data),
            "bytes": data
        }

    # --------- API pública ---------

    async def build(self, items: Iterable[Union[UploadFile, bytes, Path, BinaryIO, dict]]) -> List[FilePayload]:
        items = list(items)

        if self.max_files and len(items) > self.max_files:
            raise HTTPException(400, f"Máximo de {self.max_files} arquivos permitido.")

        payloads: List[FilePayload] = []

        for item in items:
            if isinstance(item, UploadFile):
                payload = await self._from_upload_file(item)
            elif isinstance(item, bytes):
                payload = self._from_bytes(item)
            elif isinstance(item, Path):
                payload = self._from_path(item)
            elif hasattr(item, "read"):
                payload = self._from_file_like(item)
            elif isinstance(item, dict):
                payload = self._from_payload(item)
            else:
                raise HTTPException(400, f"Tipo de entrada não suportado: {type(item)}")

            payloads.append(payload)

        return payloads


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

