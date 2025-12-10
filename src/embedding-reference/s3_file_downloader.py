import requests
from io import BytesIO
import os
from abc import ABC, abstractmethod

class URLValidatorStrategy(ABC):
    @abstractmethod
    def validate(self, url: str):
        pass


class HttpURLValidator(URLValidatorStrategy):
    def validate(self, url: str):
        if not url.lower().startswith(("http://", "https://")):
            raise ValueError("URL inválida: apenas URLs HTTP/HTTPS são permitidas.")

class FileDownloader:
    """
    Responsável apenas por baixar o arquivo (Single Responsibility).
    Agora: sem validação de extensão e sem limite de tamanho.
    """

    def __init__(
        self,
        url_validator: URLValidatorStrategy,
    ):
        self.url_validator = url_validator

    def download(self, url: str):
        # Validação da URL via Strategy
        self.url_validator.validate(url)

        # Realiza download
        response = self._safe_request(url)

        # Lê bytes na memória
        file_bytes = self._read_stream(response)

        # Extrai nome e extensão
        file_extension = self._extract_extension(url)

        return file_bytes, file_extension

    def _safe_request(self, url: str):
        try:
            response = requests.get(url, stream=True, timeout=15)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Erro ao baixar o arquivo: {e}")

        return response

    def _read_stream(self, response):
        file_bytes = BytesIO()

        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file_bytes.write(chunk)

        file_bytes.seek(0)
        return file_bytes

    def _extract_extension(self, url: str):
        file_name = os.path.basename(url.split("?")[0])
        extension = os.path.splitext(file_name)[-1].lower().replace(".", "")
        return extension
