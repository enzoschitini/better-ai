import os

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from typing import Optional, List
from pydantic import BaseModel

from src.web_services_network.request_resource import RequestResorse, Authorization

from src.image_generation.module import ImageGenerate, RequestProcessor

router = APIRouter(
    prefix="/davinci",
    tags=["image-generation"]
)

load_dotenv()

@router.post("/image-generation", 
          summary="Image generation based on prompts, settings, and optional images.")
async def image_generation(
    user_input: str = Form(...),
    instructions: Optional[str] = Form(None),
    config: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None)
):
    """
    Endpoint responsável pela geração de imagens a partir de um prompt textual,
    permitindo o uso de instruções adicionais, configurações customizadas e
    arquivos de referência.

    Parâmetros:
    ----------
    user_input : str
        Prompt principal que descreve a imagem a ser gerada.

    instructions : Optional[str], default=None
        Instruções adicionais para orientar o estilo ou comportamento da geração.

    config : Optional[str], default=None
        Configuração em formato JSON contendo parâmetros do modelo, como tamanho,
        modelo utilizado, qualidade, entre outros.

    files : Optional[List[UploadFile]], default=None
        Lista de arquivos de referência (ex: imagens) que podem ser utilizados
        como base para a geração.

    Fluxo:
    ------
    1. Processa a configuração e os arquivos enviados.
    2. Extrai os bytes das imagens e normaliza os parâmetros.
    3. Executa o gerador de imagens com os dados fornecidos.

    Retorno:
    -------
    Dict
        Estrutura contendo:
        - status: Código de status da requisição
        - data: Resultado da geração (imagens, metadados, etc.)
    """

    processor = RequestProcessor(config=config, files=files)
    processor_result = await processor.process()

    config_dict = processor_result["config"]
    image_bytes = processor_result["image_bytes"]

    generator = ImageGenerate(
        user_input=user_input,
        instructions=instructions,
        config=config_dict,
        image_bytes=image_bytes
    )

    response = generator.runner()

    return {
        "status": 200,
        "data": response
    }


