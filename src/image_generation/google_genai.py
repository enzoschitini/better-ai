from google import genai
import os
from dotenv import load_dotenv
import uuid
from dataclasses import dataclass
from typing import Protocol, List, Dict

load_dotenv()

class ClientGemini:
    """
    Classe responsável unicamente por inicializar o client da API.
    SRP – Single Responsibility
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY não foi definida no ambiente ou passada como parâmetro."
            )

        self.client = genai.Client(api_key=self.api_key)


class ModelRegistry:
    """
    Classe responsável por manter um catálogo de modelos.
    Segue o princípio OCP – Open/Closed.
    """

    MODELS: Dict[str, str] = {
        "ULTRA": "models/imagen-4.0-ultra-generate-001",
        "FAST": "models/imagen-4.0-fast-generate-001",
        "BASE": "models/imagen-4.0-generate-001",
    }

    @classmethod
    def get(cls, name: str) -> str:
        name = name.upper()
        if name not in cls.MODELS:
            raise ValueError(f"Modelo '{name}' não encontrado no registry.")
        return cls.MODELS[name]


@dataclass
class ImagePayload:
    """
    DTO para validação de payload de geração de imagem.
    """

    prompt: str
    number_of_images: int = 1  # Max 4
    aspect_ratio: str = "1:1"
    image_size: str = "1K"
    #person_generation: str = "allow_all"
    model: str = "FAST"

    def validate(self):
        if not self.prompt:
            raise ValueError("Prompt é obrigatório.")

        if not 1 <= self.number_of_images <= 4:
            raise ValueError("number_of_images deve ser entre 1 e 4.")

        if self.aspect_ratio not in ["1:1", "9:16", "16:9", "4:3", "3:4"]:
            raise ValueError("Aspect ratio inválido.")

        #if self.person_generation not in ["dont_allow", "allow_adult", "allow_all"]:
            """
            dont_allow: Blocca la generazione di immagini di persone.
            allow_adult: Genera immagini di adulti, ma non di bambini. Questa è l'impostazione predefinita.
            allow_all: Genera immagini che includono adulti e bambini.
            
            *Nota: il valore del parametro "allow_all" non è consentito nelle località UE, Regno Unito, Svizzera e MENA.
            """
            #raise ValueError("Aspect ratio inválido.")

        if self.image_size not in ["1K", "2K"]:
            raise ValueError("Image size inválido.")


class ImageSaverProtocol(Protocol):
    """ Interface de salvamento (LSP + ISP + DIP) """
    def save(self, image_bytes: bytes) -> str:
        ...

class LocalImageSaver:
    """
    Implementação concreta de salvamento.
    OCP – novos tipos (S3, GCS, CDN) podem ser adicionados depois.
    """

    def __init__(self, base_path: str = "generated_images", domain: str | None = None):
        self.base_path = base_path
        self.domain = domain or os.environ.get("ENV_DOMINIO", "")

        os.makedirs(self.base_path, exist_ok=True)

    def save(self, image_bytes: bytes) -> str:
        filename = f"{uuid.uuid4()}.jpg"
        filepath = os.path.join(self.base_path, filename)

        with open(filepath, "wb") as f:
            f.write(image_bytes)

        # URL final
        return f"{self.domain}/{filename}" if self.domain else filepath


class ImageGenerator:
    """
    Classe especializada na geração de imagens.
    DIP – depende de abstrações, não implementações.
    """

    def __init__(self, gemini_client: ClientGemini):
        self.client = gemini_client.client

    def generate(self, payload: ImagePayload) -> List[Dict]:
        payload.validate()

        model_name = ModelRegistry.get(payload.model)

        result = self.client.models.generate_images(
            model=model_name,
            prompt=payload.prompt,
            config=dict(
                number_of_images=payload.number_of_images,
                output_mime_type="image/jpeg",
                aspect_ratio=payload.aspect_ratio,
                #personGeneration=payload.person_generation,
            ),
        )

        if not result.generated_images:
            raise RuntimeError("Nenhuma imagem foi gerada.")

        saved_images = []

        for generated in result.generated_images:
            image_bytes = generated.image.image_bytes  # <- Bytes da imagem

            # Retorno agora inclui também os bytes
            saved_images.append(
                {
                    "status": "success",
                    "nm_image": f"{str(uuid.uuid4())[:8]}.jpeg",
                    "image_bytes": image_bytes,  # <-- ADICIONADO
                }
            )

        return saved_images


class ImageGenerationService:
    """
    Camada de orquestração: recebe o payload, gera imagens e salva.
    """

    def __init__(self, api_key: str | None = None):
        self.client = ClientGemini(api_key=api_key)
        #self.saver = LocalImageSaver()
        self.generator = ImageGenerator(self.client)

    def create_image(self, payload: ImagePayload) -> List[Dict]:
        return self.generator.generate(payload)





payload = ImagePayload(
    prompt="A futuristic cyberpunk samurai walking in neon Tokyo",
    # Classe para turbinar prompt
    number_of_images=1,
    aspect_ratio="9:16",
    image_size="1K",
    model="FAST",
)

service = ImageGenerationService()

results = service.create_image(payload)

for r in results:
    print(r["nm_image"])
    path = f"{r['nm_image']}"

    with open(path, "wb") as f:
        f.write(r['image_bytes'])

"""
[
    {
        'status': 'success',
        'url': 'generated_images/8ea4e53d-a85f-45ef-8be2-146ef3ac.jpg',
        'image_bytes': b'\xFF\xD8\xFF\xE0\x00\x10JFIF...'
    }
]


results = [
    {
        'status': 'success',
        'url': 'generated_images/8ea4e53d-a85f-45ef-8be2-146ef3ac.jpg',
        'image_bytes': b'\xFF\xD8\xFF\xE0\x00\x10JFIF...'
    },
    {
        'status': 'success',
        'url': 'generated_images/8ea4e53d-a85f-45ef-8be2-146ef3ac.jpg',
        'image_bytes': b'\xFF\xD8\xFF\xE0\x00\x10JFIF...'
    }
]

for x in results:
    url = x["url"]
    image_bytes = x["image_bytes"]

    with open(url, "wb") as f:
        f.write(image_bytes)

    print(url)
    print(image_bytes)
print(result)
"""

# Doc: https://ai.google.dev/gemini-api/docs/imagen?hl=it#imagen-4



