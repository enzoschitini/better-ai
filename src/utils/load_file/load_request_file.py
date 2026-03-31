import mimetypes
from fastapi import UploadFile, HTTPException
from io import BytesIO
from src.utils.load_file.config import ALLOWED_EXTENSIONS, ALL_MIMETYPES


class LoadRequestFile:
    def __init__(
        self,
        file: UploadFile,
        allowed_extensions: list[str] = ALLOWED_EXTENSIONS,
        allowed_mimetypes: list[str] = ALL_MIMETYPES,
        max_size_mb: float = 10,
    ):
        self.file = file
        self.allowed_extensions = allowed_extensions or []
        self.allowed_mimetypes = allowed_mimetypes or []
        self.max_size_mb = max_size_mb

        self.filename = file.filename
        self.extension = self._get_extension()
        self.mimetype = file.content_type

        self.bytes = None
        self.size_bytes = 0
        self.size_mb = 0.0

    async def load(self):
        """Lê o arquivo e calcula metadados"""
        content = await self.file.read()
        self.bytes = BytesIO(content)

        self.size_bytes = len(content)
        self.size_mb = self.size_bytes / (1024 * 1024)

        self._validate()

        return self

    def _get_extension(self) -> str:
        if self.filename and "." in self.filename:
            return self.filename.rsplit(".", 1)[-1].lower()
        return ""

    def _validate(self):
        self._validate_extension()
        self._validate_mimetype()
        self._validate_size()

    def _validate_extension(self):
        if self.allowed_extensions and self.extension not in self.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Extensão '{self.extension}' não permitida. Permitidas: {self.allowed_extensions}"
            )

    def _validate_mimetype(self):
        if self.allowed_mimetypes and self.mimetype not in self.allowed_mimetypes:
            raise HTTPException(
                status_code=400,
                detail=f"Mimetype '{self.mimetype}' não permitido. Permitidos: {self.allowed_mimetypes}"
            )

    def _validate_size(self):
        if self.size_mb > self.max_size_mb:
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo excede o limite de {self.max_size_mb} MB"
            )

    def to_dict(self):
        return {
            "filename": self.filename,
            "extension": self.extension,
            "mimetype": self.mimetype,
            "size_bytes": self.size_bytes,
            "size_mb": round(self.size_mb, 2),
        }


from fastapi import FastAPI, File, UploadFile

app = FastAPI()

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    loader = LoadRequestFile(
        file,
        allowed_extensions=["txt", "pdf"],
        allowed_mimetypes=["text/plain", "application/pdf"],
        max_size_mb=5,
    )
    result = await loader.load()
    return result.to_dict()
    
"""
curl -X POST "http://127.0.0.1:8000/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@caminho/do/seu/arquivo.txt"
"""

    # uvicorn src.utils.load_file.load_request_file:app --reload 