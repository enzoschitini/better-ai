from google import genai
import os
from dotenv import load_dotenv
import uuid
from dataclasses import dataclass
from typing import Protocol, List, Dict
import base64
import requests

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
    number_of_images: int
    aspect_ratio: str
    image_size: str
    #person_generation: str = "allow_all"
    model: str

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

    def save_image(self, results):
        url = "https://better-ai-bucket-storage-production.up.railway.app/save-images"
        base_url = "http://better-ai-bucket-storage-production.up.railway.app/images"

        formatted_results = []

        for image in results:
            formatted_results.append({
                "nm_image": image["nm_image"],
                "image_bytes": base64.b64encode(image["image_bytes"]).decode("utf-8")
            })

        payload = {
            "results": formatted_results
        }

        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                images_urls = [
                    f"{base_url}/{img['nm_image']}" for img in formatted_results
                ]

                return {
                    "status": 200,
                    "images": images_urls
                }

            return {
                "status": response.status_code,
                "response": response.text
            }

        except requests.exceptions.RequestException as e:
            return {
                "status": 500,
                "error": str(e)
            }


    def generate(self, prompt, number_of_images, aspect_ratio, image_size, model):
        try:
            payload = ImagePayload(
                prompt=prompt,
                number_of_images=number_of_images,
                aspect_ratio=aspect_ratio,
                image_size=image_size,
                model=model,
            )

            service = ImageGenerationService()
            results = service.create_image(payload)

        except Exception as e:
            return {
                "status": 500,
                "error": f"Erro ao gerar imagem: {str(e)}"
            }

        try:
            r = self.save_image(results=results)
            return r
        
        except Exception as e:
            return {
                "status": 500,
                "error": f"Erro ao salvar imagem: {str(e)}"
            }

        # {'status': 200, 'images': ['http://better-ai-bucket-storage-production.up.railway.app/images/d0b1da59.jpeg']}


# Doc: https://ai.google.dev/gemini-api/docs/imagen?hl=it#imagen-4