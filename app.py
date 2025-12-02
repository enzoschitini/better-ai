from fastapi import FastAPI, UploadFile, HTTPException, Request, Form, Depends, Header, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
import json
import os
import uuid
import logging

from  src.chat.AgentAsk import AgentAsk
from src.embbeding.embedding import embedding_documents
from src.image_generation.google_genai import ImageGenerationService

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

# uvicorn app:app --reload
# http://127.0.0.1:8000

def get_authorization_betterai_api(authorization: str = Header(...)):
    betterai_api_key = os.getenv("BETTERAI_API_KEY") # betterai-api-key
    
    if authorization != f"Bearer {betterai_api_key}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return authorization



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
@app.post("/run-agent", dependencies=[Depends(get_authorization_betterai_api)], response_model=AgentRunResponse)
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

"""
curl --location 'http://127.0.0.1:8000/run-agent' \
--header 'Content-Type: application/json' \
--data '{
    "input_text": "Valeu",
    "business_id": "0011",
    "metadata": {"client_id": "1234"},
    "user_prompt": "Você é um agente de IA",
    "temperature": 0.5,
    "tool_kit": ["retorna_temperatura_atual","busca_wikipedia", "AnswerGeneration"],
    "tool_dic": {
      "retorna_temperatura_atual": {"city": "São Paulo", "units": "metric"},
      "AnswerGenerationDic": {"filter_search": {"file_id": "file_id_01"}}
    },
    "session_id": null,
    "streaming": false
  }'
"""







@app.post("/embedding_file", dependencies=[Depends(get_authorization_betterai_api)], response_model=AgentRunResponse)
async def upload_file(
    metadata: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Endpoint that receives a JSON metadata dictionary and a file.
    The file name and extension are automatically extracted.
    """

    # Parse metadata JSON string into a Python dictionary
    try:
        metadata_dict = json.loads(metadata)
    except json.JSONDecodeError:
        logging.error("The 'metadata' field must contain valid JSON.")
        logging.error("")
        return JSONResponse(
            status_code=400,
            content={"error": "The 'metadata' field must contain valid JSON."}
        )

    # Read file content asynchronously
    file_content = await file.read()
    
    embedding_result = embedding_documents(metadata_dict, file_content, file)

    # Build response
    response = {
        "message": "File uploaded successfully!",
        "metadata": metadata_dict,
        "embedding_result": embedding_result
    }

    return JSONResponse(content=response)



"""
curl --location 'http://127.0.0.1:8000/embedding_file' \
--header 'accept: application/json' \
--form 'metadata="{\"embedding_filter\": {\"file_ids\": \"1234\", \"collection_id\": \"22\"}, \"embedding_aggregations\": {\"collection_name\": \"Babbel\"}}"' \
--form 'file=@"/C:/Users/schit/Downloads/Group 1321314784.png"'


{
    "message": "File uploaded successfully!",
    "metadata": {
        "embedding_filter": {
            "file_ids": "1234",
            "collection_id": "22",
            "file_id": "62e8d769-f110-49f0-ab91-3b46f0d2e0f8"
        },
        "embedding_aggregations": {
            "collection_name": "Babbel",
            "file_name": "Group 1321314784",
            "file_extension": "png"
        }
    }
}
"""
# uvicorn app:app --reload
# http://127.0.0.1:8000





@app.get("/generate-id", dependencies=[Depends(get_authorization_betterai_api)])
def generate_id():
    """
    Gera e retorna um UUID v4 como string.
    """
    new_id = str(uuid.uuid4())
    return {"id": new_id}

"""
curl http://127.0.0.1:8000/generate-id
"""



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
    "/generate-image", dependencies=[Depends(get_authorization_betterai_api)],
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

"""
uvicorn app:app --reload
http://127.0.0.1:8000

curl --location 'http://localhost:8000/generate-image' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer 2afd6752-2b39-468e-b27b-d67b77fddd3f-3f105e35-a345-4c12-8018-9aebaa3522ed' \
--data '{
    "prompt": "A bowl of Italian tomato sauce, of the type of tomato sauce, on a bench of a vibrant cozinha from the 1960s. The bowl must be a focal point, with authentic Italian rolls and a soft shine. On the grill, use vintage cooking utensils, such as a metal egg beater or a cooking knife, and sometimes some fresh ingredients such as tough and tasty tomatoes. The lighting must be bright, with a touch of solar light entering a woman with geometric door curtains characteristic of the era. The style must be photorealistic with meticulous attention to details, textures and cores, capturing the nostalgia and simplicity of the Italian lifestyle of the 60s.",
    "number_of_images": 2,
    "aspect_ratio": "9:16",
    "image_size": "2K",
    "model": "ULTRA"
  }'

curl --location --request DELETE 'https://better-ai-bucket-storage-production.up.railway.app/delete-images'

{
    "status": 200,
    "images": [
        "http://better-ai-bucket-storage-production.up.railway.app/images/518369fb.jpeg",
        "http://better-ai-bucket-storage-production.up.railway.app/images/bb5b1655.jpeg"
    ]
}
"""
















# TEST AUTHORIZATION


# uvicorn app:app --reload
# http://127.0.0.1:8000


def get_authorization_mult_key(
    authorization: str = Header(...),
    company_id: str = Header(..., alias="company-id"),
    company_key: str = Header(..., alias="company-key")
):
    # Chave master  
    betterai_api_key = os.getenv("BETTERAI_API_KEY")

    # Chave específica da empresa
    secret_key_env = os.getenv(f"{company_id.upper()}_SECRET_KEY")

    # Verifica BETTERAI_API_KEY
    if authorization != f"Bearer {betterai_api_key}":
        raise HTTPException(status_code=401, detail="Invalid Authorization Key")

    # Verifica SECRET_KEY da empresa
    if company_key != f"Bearer {secret_key_env}":
        raise HTTPException(status_code=401, detail="Invalid Company Secret Key")

    return True


from auth import Authorization

@app.get("/healthy-authorization", dependencies=[Depends(Authorization.multikey)])
def healthy_authorization():
    return {"status": "ok"}

# ✅ Endpoint health check
"""
curl -X GET "http://127.0.0.1:8000/healthy"

curl -X GET "http://127.0.0.1:8000/healthy-authorization" \
  -H "Authorization: Bearer betterai-api-key"
"""

@app.get("/healthy")
def healthy():
    return {"status": "ok"}




# Enzo Schitini