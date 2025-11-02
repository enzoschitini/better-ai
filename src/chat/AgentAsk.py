# =========================================
# IMPORTS
# =========================================
import time
import uuid
from datetime import datetime
from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig

from src.chat.tools.tools import get_tools_config
from src.chat.buffer_memory import save_chat_history
import warnings

from src.chat.InitializeAgent import initialize_agent

from src.chat.tokens_calculator.tokens_estimated import estimar_tokens_completos
from src.chat.utils.business_verifier import BusinessVerifier

# Ignora todos os warnings
warnings.filterwarnings("ignore")

# Ou apenas warnings específicos de UserWarning
warnings.filterwarnings("ignore", category=UserWarning)

load_dotenv()

# =========================================
# EXECUÇÃO DO AGENTE (STREAMING + TOOLS + MEMÓRIA)
# =========================================
def AgentAsk(input_text: str, business_id: str, metadata: dict, user_prompt: str, temperature: float,
             tool_kit: list, tool_dic: dict,
             session_id: str = None, streaming: bool = False):
    
    """Executa o chat com memória, tools, streaming e salva log detalhado."""

    verificador = BusinessVerifier("src/chat/tokens_calculator/business_acess.json")
    status_plan = verificador.verificar(business_id)

    """
    if status_plan != "activated":
        return {
            "message": "Desculpa! O plano da sua empresa não está ativo. Por favor, entre em contato com o suporte para mais informações.",
            "session_id": session_id,
            "status": "error",
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    #"""

    inicio = time.time()
    session_id = session_id or str(uuid.uuid4())

    try:
        # Tools configuradas
        tools, tools_json, tool_run = get_tools_config(tool_kit, tool_dic)

        # Inicializa agente
        agent_executor, memory, session_id, handler, system_prompt = initialize_agent(
            session_id, user_prompt, temperature, tools, tools_json, tool_run, streaming=streaming
        )

        """
        config = RunnableConfig(
            tags=["pipeline-curiosidade-historia"],
            metadata={
                "autor": "Enzo Schitini",
                "versao_pipeline": "2.0-mongo",
                "projeto": "Scituffy",
                "tipo_execucao": "produção"
            }
        )
        """

        # Executa o agente
        response = agent_executor.invoke({'input': input_text})
        tempo_execucao = round(time.time() - inicio, 2)

        save_chat_history(session_id, memory)
        final_text = handler.get_response() if streaming else response.get("output", "")

        # Log final
        log_data = {
            "session_id": session_id,
            "business_id": business_id,
            "metadata": metadata,
            "input": input_text,
            "response": final_text,
            "tempo_execucao_s": tempo_execucao,
            "status": "success",
        }

        tool_respose = ""
        tool_tokens_used = 0

        if response.get("intermediate_steps"):
            log_data["tool"] = response["intermediate_steps"][0][0].tool
            log_data["tool_output"] = str(response["intermediate_steps"][0][1])
            tool_respose = response["intermediate_steps"][0][1]["response"]

            if "tokens_used" in response["intermediate_steps"][0][1]:
                tool_tokens_used += response["intermediate_steps"][0][1]["tokens_used"]

        # Tokens estimados
        tokens_response = estimar_tokens_completos(
            system_prompt=system_prompt,
            chat_history=memory.chat_memory.messages,
            tools_json=tools_json,
            tool_response=tool_respose,  # <-- CORRIGIDO AQUI
            tool_tokens_used=tool_tokens_used
        )

        log_data["tokens_estimados"] = tokens_response

        from src.chat.tokens_calculator.main import menage_chat_usage
        import json
        import threading

        #print(json.dumps(log_data, indent=4, ensure_ascii=False))

        # Executa em segundo plano sem bloquear
        threading.Thread(
            target=menage_chat_usage,
            args=(business_id, "gpt-4o-mini", log_data),
            daemon=True
        ).start()

        #salvar_log_json(log_data)

        return log_data

    except Exception as e:
        erro_log = {
            "session_id": session_id,
            "erro": str(e),
            "status": "error",
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        #salvar_log_json(erro_log)
        return {
            "message": "Desculpa! Não foi possivel responder a pergunta. Por favor tente novamente.",
            "session_id": session_id,
            "erro": str(e),
            "status": "error",
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }