from fastapi import FastAPI, UploadFile, HTTPException, Request, Form, Depends, Header, File
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json

from src.chat.AgentAsk import AgentAsk


app = FastAPI(
    title="BetterAI Chat API",
    description="""
API para interação com o agente de IA BetterAI 🤖  
Permite o envio de mensagens e manutenção de contexto de sessão entre interações.
    """,
    version="1.0.0"
)

# uvicorn app:app --reload
# http://127.0.0.1:8000

def get_authorization_betterai_api(authorization: str = Header(...)):
    if authorization != "Bearer betterai-api-key":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return authorization






# ======== MODELOS DE ENTRADA ========
class AgentAskRequest(BaseModel):
    input_text: str = Field(..., description="Texto de entrada do usuário")
    business_id: str = Field(..., description="Identificador do negócio")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadados adicionais")
    user_prompt: Optional[str] = Field(default="Você é um agente de IA", description="Instrução para o modelo")
    temperature: Optional[float] = Field(default=0.5, description="Temperatura de geração")
    tool_kit: Optional[List[str]] = Field(default_factory=list, description="Lista de ferramentas disponíveis para o agente")
    # Aqui aceitamos qualquer chave/valor — flexível para ferramentas variáveis
    tool_dic: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Dicionário de configuração dinâmico das ferramentas")
    session_id: Optional[str] = Field(default=None, description="ID da sessão para manter o contexto")
    streaming: Optional[bool] = Field(default=False, description="Se True, habilita streaming de resposta")


# ======== MODELOS DE SAÍDA ========
class AgentAskResponse(BaseModel):
    session_id: str
    response: Dict[str, Any]


# ======== ENDPOINT ========
@app.post("/agentask", response_model=AgentAskResponse)
def execute_agentask(request: AgentAskRequest):
    """
    Executa o agente de IA com os parâmetros fornecidos.
    tool_dic é livre — aceita qualquer estrutura de dicionário para ferramentas.
    """
    try:
        # chama AgentAsk passando exatamente o dict recebido
        resposta = AgentAsk(
            input_text=request.input_text,
            business_id=request.business_id,
            metadata=request.metadata,
            user_prompt=request.user_prompt,
            temperature=request.temperature,
            tool_kit=request.tool_kit,
            tool_dic=request.tool_dic,   # já é um dict flexível
            session_id=request.session_id,
            streaming=request.streaming
        )

        # Validação simples: garantir que session_id exista na resposta
        #if "session_id" not in resposta:
            #raise ValueError("AgentAsk retornou resposta sem 'session_id'.")

        return AgentAskResponse(
            session_id=resposta["session_id"],
            response=resposta
        )

    except Exception as e:
        # Retornamos erro com 500 para facilitar debug do cliente
        raise HTTPException(status_code=500, detail=str(e))





































# ---- MODELOS TIPADOS ----
class AgentAskInput(BaseModel):
    input_text: str
    business_id: str
    session_id: str | None = None  # opcional — mantém a memória da sessão

class AgentAskOutput(BaseModel):
    session_id: str
    response: dict

# ---- ENDPOINT ----
@app.post("/chat", response_model=AgentAskOutput)
def chat_with_agent(data: AgentAskInput):
    """
    Endpoint para interagir com o agente de IA.
    Mantém a sessão caso o mesmo session_id seja reutilizado.
    """
    try:
        resposta = AgentAsk(
            input_text=data.input_text,
            business_id=data.business_id,
            session_id=data.session_id
        )

        # Garante que a resposta é um dict
        if isinstance(resposta, str):
            try:
                resposta = json.loads(resposta)
            except json.JSONDecodeError:
                resposta = {"message": resposta}

        return AgentAskOutput(
            session_id=resposta.get("session_id", data.session_id or "unknown"),
            response=resposta
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no agente: {str(e)}")

"""
curl -X POST "http://127.0.0.1:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{
           "input_text": "Olá, tudo bem?",
           "business_id": "0010",
           "session_id": null
         }'
"""
















class CiSei(BaseModel):
    message: str
    valore: int

@app.post("/ci-sei", dependencies=[Depends(get_authorization_betterai_api)])
def ci_sei(request: CiSei):
    result = request.valore * 2 + 1
    return {"message": request.message, "result": result}

"""
curl -X POST "http://127.0.0.1:8000/ci-sei" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer betterai-api-key" \
  -d '{
    "message": "Olá, estou aqui!",
    "valore": 21
  }'
"""






















# ✅ Endpoint health check
"""
curl -X GET "http://127.0.0.1:8000/healthy"

curl -X GET "http://127.0.0.1:8000/healthy-authorization" \
  -H "Authorization: Bearer betterai-api-key"
"""

@app.get("/healthy")
def healthy():
    return {"status": "ok"}

@app.get("/healthy-authorization", dependencies=[Depends(get_authorization_betterai_api)])
def healthy_authorization():
    return {"status": "ok"}



