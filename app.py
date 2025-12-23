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

from auth import Authorization
from src.chat.AgentAsk import AgentAsk

from src.embedding.embedding_module import EmbeddingModule
from src.embedding.services.pinecone_vector_store import PineconeClient, PineconeVectorService

from src.image_generation.google_genai import ImageGenerationService
from src.embedding.services.payload_validation import PayloadProcessor

# ================================================
# API SETTINGS
# ================================================

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(filename)s - line: %(lineno)d - %(levelname)s - %(message)s'
)

logging.info("Application started!")

app = FastAPI(
    title="BetterAI Chat API",
    description="""
API para interação com o agente de IA BetterAI 🤖  
Permite o envio de mensagens e manutenção de contexto de sessão entre interações.
    """,
    version="1.0.0"
)

# Lista de domínios confiáveis (coloca aqui apenas os que realmente vão acessar a API)
origins = [
    "https://better-ai.up.railway.app",
    "https://better-ai-homol.up.railway.app",
    "https://better-ai-dev.up.railway.app",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,         # apenas origens confiáveis
    allow_credentials=True,        # habilita envio de cookies/autenticação
    allow_methods=["GET", "POST"], # apenas os métodos realmente usados
    allow_headers=["Authorization", "Content-Type"],  # cabeçalhos necessários
)

load_dotenv()



# ================================================
# SERVICES
# ================================================


@app.get("/generate-id", dependencies=[Depends(Authorization.multikey)])
def generate_id():
    """
    Gera e retorna um UUID v4 como string.
    """
    new_id = str(uuid.uuid4())
    return {"id": new_id}


# ========================
# MODELO DE ENTRADA
# ========================
class AgentRunRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="ID da sessão para manter o contexto da conversa")
    business_id: str = Field(..., description="Identificador único do negócio")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadados adicionais sobre o cliente ou contexto")
    input_text: str = Field(..., description="Texto de entrada fornecido pelo usuário")
    user_prompt: Optional[str] = Field(default="Você é um agente de IA", description="Instrução de comportamento para o modelo")
    temperature: Optional[float] = Field(default=0.5, description="Temperatura de geração do modelo (controle de aleatoriedade)")
    tool_kit: Optional[List[str]] = Field(default_factory=list, description="Lista de ferramentas disponíveis para o agente")
    tool_dic: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Dicionário de configurações dinâmicas das ferramentas")
    streaming: Optional[bool] = Field(default=False, description="Se True, habilita resposta em streaming")


# ========================
# MODELO DE SAÍDA
# ========================
class AgentRunResponse(BaseModel):
    response: Dict[str, Any]


# ========================
# ENDPOINT PRINCIPAL
# ========================
@app.post("/run-agent", dependencies=[Depends(Authorization.multikey)], response_model=AgentRunResponse)
def run_agent(request: AgentRunRequest):
    """
    Executa o agente de IA com os parâmetros fornecidos.
    - `tool_dic` é dinâmico e pode conter qualquer estrutura.
    - Mantém contexto entre requisições via `session_id`.
    """
    try:
        result = AgentAsk(
            input_text=request.input_text,
            business_id=request.business_id,
            metadata=request.metadata,
            user_prompt=request.user_prompt,
            temperature=request.temperature,
            tool_kit=request.tool_kit,
            tool_dic=request.tool_dic,
            session_id=request.session_id,
            streaming=request.streaming
        )

        return AgentRunResponse(
            response=result
        )

    except Exception as e:
        logging.error("Erro ao executar o agente: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao executar o agente: {e}"
        )



# ========================
# Embedding Services
# ========================

class EmbeddingPayload(BaseModel):
    data: Dict[str, Any]

    class Config:
        extra = "allow"


class EmbeddingResponse(BaseModel):
    status: str
    file_id: str
    mongo_id: str

@app.post("/embedding-file", response_model=EmbeddingResponse, dependencies=[Depends(Authorization.multikey)], 
          summary="It processes the uploaded file, generates vector embeddings, and stores them in a vector database.")

async def embedding_file(
    request: Request,
    payload: str = Form(...),
    file: UploadFile = File(...)
):
    # Ensures that only 1 file was sent.
    form = await request.form()
    files = form.getlist("file")

    if len(files) > 1:
        raise HTTPException(
            status_code=400,
            detail="Only one file is allowed"
        )

    # Validates if the payload is valid JSON.
    try:
        payload_dict = json.loads(payload)
        payload_obj = EmbeddingPayload(data=payload_dict)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid payload JSON: {str(e)}"
        )

    # Checks if the file has arrived.
    if not file or not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File is required"
        )

    # Process file
    try:
        payload_processor = PayloadProcessor(payload_obj.data)
        valid_payload = payload_processor.process()

        module = EmbeddingModule(
            payload=valid_payload,
            file=file
        )
        
        result = await module.execute()
        return result

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# ========================
# Delete
# ========================

class DeleteVectorsResponse(BaseModel):
    deleted_vectors: int = Field(..., description="Quantidade de vetores removidos")
    message: str = Field(..., description="Mensagem de confirmação da operação")

@app.post("/delete-vectors", response_model=DeleteVectorsResponse, dependencies=[Depends(Authorization.multikey)],
          summary="Excludes vectors indexed in Pinecone using metadata filters."
)
async def delete_vectors(
    target_feature: str = Form(...),
    target_id: str = Form(...),
    namespace: str = Form(...)
):
    pine_client = PineconeClient(
        index_name=os.getenv("PINECONE_INDEX_NAME"),
        namespace=os.getenv("PINECONE_NAMESPACE"),
        global_namespace=os.getenv("PINECONE_GLOBAL_NAMESPACE")
    )

    pine_service = PineconeVectorService(
        vector_client=pine_client,
        embedding_model_name="text-embedding-3-large",
        dimensions=3072
    )

    response = pine_service.delete_documents(target_feature, target_id, namespace)

    return response






# ========================
# Image Generate
# ========================

class GenerateRequest(BaseModel):
    prompt: str
    number_of_images: int
    aspect_ratio: Literal["1:1", "9:16", "16:9", "4:3", "3:4"]
    image_size: Literal["1K", "2K"]
    model: Literal["FAST", "BASE", "ULTRA"]

class GenerateResponse(BaseModel):
    status: int
    images: List[str]

@app.post(
    "/generate-image", dependencies=[Depends(Authorization.multikey)],
    response_model=GenerateResponse,
    summary="Gera imagens com parâmetros fixos"
)
def generate_image(data: GenerateRequest) -> GenerateResponse:
    gen = ImageGenerationService()

    return gen.generate(
        prompt=data.prompt,
        number_of_images=data.number_of_images,
        aspect_ratio=data.aspect_ratio,
        image_size=data.image_size,
        model=data.model
    )

















# Endpoint health check:

@app.get("/healthy")
def healthy():
    return {"status": "ok"}

@app.get("/healthy-authorization", dependencies=[Depends(Authorization.multikey)])
def healthy_authorization():
    return {"status": "ok"}


# Author: Enzo Schitini