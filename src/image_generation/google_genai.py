from google import genai
import os
from dotenv import load_dotenv
import uuid

load_dotenv()

class ClientGemini:
    """
    Classe simples para inicializar o cliente do Gemini.

    Ex:
    client = ClientGemini()
    print(client.client)
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY não foi definida no ambiente ou passada como parâmetro."
            )

        self.client = genai.Client(api_key=self.api_key)

class Models:
    """
    Classe para controle e melhor gestão dos modelos

    QUero selecionar os modelos tanto passando tipo um metodo ponto "." e o modelo e também passando o nome. Ou então associação por dicionario com o nome "Comercial" e o nome real do modelo
    """

    def __init__(self):
        pass

    # imagen-4.0-ultra-generate-001
    # imagen-4.0-fast-generate-001
    # imagen-4.0-generate-001

class SaveImage:
    """
    Classe que salva a imagem em uma pasta e retorna uma URL da imagem salva com a estrutura (URL: {ENV_DOMINIO}/nome_imagem.extensão)
    com o nome partido de um UUID4

    O retono é um staus se deu certo, onde salvou, qual o nome: uuid.extensão e também a url
    """

class ImageGeneration:
    """
    Classe composta por diversos metodos para elaboração da imagem
    """

    def __init__(self):
        pass

    # Validation Payload
    number_of_images = 4 # Max 4
    aspect_ratio = ["1:1", "9:16", "16:9", "4:3", "3:4"]
    image_size = ["1K", "2K"]





# Base:

def generate():
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    result = client.models.generate_images(
        model="models/imagen-4.0-fast-generate-001",
        prompt=PROMPT,
        config=dict(
            number_of_images=2,
            output_mime_type="image/jpeg",
            aspect_ratio="9:16",
        ),
    )

    if not result.generated_images:
        print("No images generated.")
        return

    if len(result.generated_images) != 2:
        print("Number of images generated does not match the requested number.")

    for n, generated_image in enumerate(result.generated_images):
        generated_image.image.save(f"imagen4-fast/{id_generation()}_{n}.jpg")


