import os
from dataclasses import dataclass, field
from typing import Optional

from google import genai
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

@dataclass
class GeminiConfig:
    api_key_env: str = "GEMINI_API_KEY"

    def get_api_key(self) -> str:
        api_key = os.getenv(self.api_key_env)

        if not api_key:
            raise EnvironmentError(
                f"Variável de ambiente '{self.api_key_env}' não encontrada."
            )

        return api_key

@dataclass
class GeminiClient:
    config: GeminiConfig = field(default_factory=GeminiConfig)  # 👈 AQUI
    _client: Optional[genai.Client] = None

    def get_client(self) -> genai.Client:
        if self._client is None:
            api_key = self.config.get_api_key()
            self._client = genai.Client(api_key=api_key)

        return self._client
