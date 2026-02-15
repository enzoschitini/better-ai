import json
import os
import uuid
import logging

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from dotenv import load_dotenv

from fastapi import FastAPI, UploadFile, HTTPException, Request, Form, Depends, Header, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="BetterAI API LAUNCH",
    description="""
API para interação com o agente de IA BetterAI 🤖  
Permite o envio de mensagens e manutenção de contexto de sessão entre interações.
    """,
    version="1.0.0"
)

# uvicorn launch_api:app --reload  

from src.image_generation.module import ImageGenerate, RequestProcessor


@app.post("/davinci/image-generation", 
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

"""
curl --location 'http://127.0.0.1:8000/davinci/image-generation' \
--header 'accept: application/json' \
--form 'user_input="Una banda di ragazzini sotto i 10 anni che giocano per strada. Devono esserci 3 quadratini sopra e due sotto, metti anche le batute con i dialoghi."' \
--form 'instructions="Lo stile deve essere fumetto per bambini"' \
--form 'config="{
    \"model\": \"gemini-2.5-flash-image\",
    \"temperature\": 0.75,
    \"top_p\": 0.85,
    \"max_output_tokens\": 1024,
    \"aspect_ratio\": \"16:9\",
    \"number_of_images\": 1
}"' \
--form 'files=@"/C:/Users/schit/Downloads/Linkedin Profilo.jpeg"' \
--form 'files=@"/C:/Users/schit/Downloads/IMG-20230714-WA0007.jpg"'
"""

