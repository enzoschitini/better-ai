from src.chat.AgentAsk import AgentAsk


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
@app.post("/run-agent", 
          #dependencies=[Depends(Authorization.multikey)], 
          response_model=AgentRunResponse
        )
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
