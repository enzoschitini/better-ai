```python
import mimetypes
from fastapi import UploadFile, HTTPException
from io import BytesIO
from src.utils.load_file.config import ALLOWED_EXTENSIONS, ALL_MIMETYPES


class LoadRequestFile:
    """
    Class responsible for loading and validating files sent in a request, checking
    file extension, MIME type, and maximum allowed size.

    Args:
        file (UploadFile): File sent in the request.
        allowed_extensions (list[str]): List of allowed file extensions. Default is ALLOWED_EXTENSIONS.
        allowed_mimetypes (list[str]): List of allowed MIME types. Default is ALL_MIMETYPES.
        max_size_mb (float): Maximum allowed file size in megabytes. Default is 10.

    Methods:
        load(): Loads the file content, calculates its metadata, and performs validations.
    """
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
        """Reads the file and calculates metadata."""
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
                detail={
                    "message": f"The '{self.extension}' extension is not allowed.",
                    "allowed_extensions": self.allowed_extensions
                }
            )

    def _validate_mimetype(self):
        if self.allowed_mimetypes and self.mimetype not in self.allowed_mimetypes:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": f"The '{self.mimetype}' mimetype is not allowed.",
                    "allowed_mimetypes": self.allowed_mimetypes
                }
            )

    def _validate_size(self):
        if self.size_mb > self.max_size_mb:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": f"The file exceeds the limit of {self.max_size_mb} MB"
                }
            )

    def to_dict(self):
        return {
            "filename": self.filename,
            "extension": self.extension,
            "mimetype": self.mimetype,
            "size_bytes": self.size_bytes,
            "size_mb": round(self.size_mb, 2),
        }
```