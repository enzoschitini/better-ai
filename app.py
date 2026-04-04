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

# Utils
from src.utils.load_file.load_request_file import LoadRequestFile

from src.chat.AgentAsk import AgentAsk

# Embedding Packages
from src.embedding.services.payload_validation import PayloadProcessor
from src.embedding.services.pinecone_vector_store import PineconeClient, PineconeVectorService
from src.embedding.embedding_module import EmbeddingModule

# Image Generation Packages (Da-Vinci)
from src.image_generation.applications import ImageGeneration
from src.image_generation.module import ImageGenerate, RequestProcessor

# Text Parser Packages
from src.content_parse.module.applications import DocumentParse

# Deep Research Packages
from src.deep_research.tavily_research.tavily_core import TavilyDeepResearch
from src.deep_research.tavily_research.context_builder import TavilyContextBuilder, TavilyResearchRunner


# ================================================
# API SETTINGS
# ================================================

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(filename)s - line: %(lineno)d - %(levelname)s - %(message)s'
)

logo = """
\033[97m
╔═════════════════════════════════════════════════════════════════════════╗

    ██████╗ ███████╗████████╗████████╗███████╗██████╗      █████╗ ██╗ ✦
    ██╔══██╗██╔════╝╚══██╔══╝╚══██╔══╝██╔════╝██╔══██╗    ██╔══██╗██║
    ██████╔╝█████╗     ██║      ██║   █████╗  ██████╔╝    ███████║██║
    ██╔══██╗██╔══╝     ██║      ██║   ██╔══╝  ██╔══██╗    ██╔══██║██║
    ██████╔╝███████╗   ██║      ██║   ███████╗██║  ██║    ██║  ██║██║
    ╚═════╝ ╚══════╝   ╚═╝      ╚═╝   ╚══════╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝

╚═════════════════════════════════════════════════════════════════════════╝

                    ✦  Where intelligence finds purpose. ✦
\033[0m
"""
logging.info(logo)

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
    client_id: str = Field(..., description="Identificador único do negócio")
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
            client_id=request.client_id,
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
    "/generate-image", 
    response_model=GenerateResponse,
    dependencies=[Depends(Authorization.multikey)],
    summary="Gera imagens com parâmetros fixos"
)
def generate_image(data: GenerateRequest) -> GenerateResponse:
    model_map = {
        "FAST": "imagen-4.0-fast-generate-001",
        "BASE": "imagen-4.0-generate-001",
        "ULTRA": "imagen-4.0-ultra-generate-001"
    }
    
    selected_model = model_map.get(data.model)

    try:
        generater = ImageGeneration()

        urls = generater.gen(
            prompt=data.prompt,
            model=selected_model,
            number_of_images=data.number_of_images,
            aspect_ratio=data.aspect_ratio,
            image_size=data.image_size,
        )

        response_obj = GenerateResponse(
            status=200,
            images=urls
        )

        return response_obj

    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro interno: {str(e)}"
        )

# DAVINCI 🍌

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


# ========================
# Context Parser
# ========================

@app.post("/parse-content/document-parse", dependencies=[Depends(Authorization.multikey)],
          summary="Parse and extract structured content from files using schema")
async def document_parse(
    job_id: str = Form(...),
    metadata: str = Form(...),
    schema: str = Form(...),
    file: UploadFile = File(...),
    config: Optional[str] = Form(None),
):
    try:
        loader = await LoadRequestFile(
            file=file,
            allowed_extensions=["txt", "md", "pdf", "docx"],
            max_size_mb=5
        ).load()

        file_bytes = loader.bytes
        file_extension = loader.extension

        parser = DocumentParse(
            job_id=job_id,
            metadata=metadata,
            schema=schema,
            config=config,
            file_bytes=file_bytes,
            file_extension=file_extension
        )

        result = parser.run()

        return JSONResponse(content={
            "status": "success",
            "job_id": result.get("job_id"),
            "result": result.get("content")
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========================
# Deep Research Context
# ========================

class ContextBuilderRequest(BaseModel):
    query: str
    search_depth: str = "advanced"
    max_results: int = 35
    topic: str = "general"
    include_answer: bool = True
    min_score: float = 0.5


@app.post("/deep-research/context-builder", dependencies=[Depends(Authorization.multikey)],
          summary="Builds context for deep research using TavilyDeepResearch.")
def context_builder(payload: ContextBuilderRequest):
    try:
        researcher = TavilyDeepResearch(
            api_key=os.getenv("TAVILY_API_KEY")
        )

        builder = TavilyContextBuilder(
            researcher=researcher,
            min_score=payload.min_score
        )

        runner = TavilyResearchRunner(builder)

        markdown_context = runner.run(
            query=payload.query,
            search_depth=payload.search_depth,
            max_results=payload.max_results,
            topic=payload.topic,
            include_answer=payload.include_answer
        )

        return {
            "status": 200,
            "query": payload.query,
            "result": markdown_context
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )







# Endpoint health check:

@app.get("/healthy")
def healthy():
    return {"status": "ok"}

@app.get("/healthy-authorization", dependencies=[Depends(Authorization.multikey)])
def healthy_authorization():
    return {"status": "ok"}


# Author: Enzo Schitini