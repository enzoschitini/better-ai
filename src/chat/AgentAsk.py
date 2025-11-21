# =========================================
# IMPORTS
# =========================================
import time
import uuid
from datetime import datetime
import json
import threading
from dotenv import load_dotenv

from langchain_core.runnables import RunnableConfig

import warnings
import logging

from src.chat.InitializeAgent import initialize_agent
from src.chat.tools.tools import get_tools_config
from src.chat.buffer_memory import save_chat_history

from src.chat.tokens_calculator.main import menage_chat_usage
from src.chat.tokens_calculator.tokens_estimated import estimar_tokens_completos
from src.chat.utils.business_verifier import BusinessVerifier
from src.chat.utils.logging_utils import setup_logging

# Ignora todos os warnings
warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", category=UserWarning)

load_dotenv()

setup_logging()


# =========================================
# EXECUÇÃO DO AGENTE (STREAMING + TOOLS + MEMÓRIA)
# =========================================
def AgentAsk(input_text: str, business_id: str, metadata: dict, user_prompt: str, temperature: float,
             tool_kit: list, tool_dic: dict,
             session_id: str = None, streaming: bool = False):
    
    logging.info(f"=== Iniciando AgentAsk() ===")
    logging.info(f"Entrada recebida | empresa={business_id} | session_id={session_id} | streaming={streaming}")

    verificador = BusinessVerifier("src/chat/tokens_calculator/business_acess.json")
    status_plan = verificador.verificar(business_id)
    logging.info(f"Status do plano da empresa ({business_id}): {status_plan}")

    inicio = time.time()
    session_id = session_id or str(uuid.uuid4())
    logging.debug(f"Session ID definido: {session_id}")

    try:
        # Tools configuradas
        logging.info("Carregando tools de configuração...")
        tools, tools_json, tool_run = get_tools_config(tool_kit, tool_dic)
        logging.debug(f"Tools carregadas com sucesso ({len(tools)} ferramentas).")

        # Inicializa agente
        logging.info("Inicializando agente LLM...")
        agent_executor, memory, session_id, handler, system_prompt = initialize_agent(
            session_id, user_prompt, temperature, tools, tools_json, tool_run, streaming=streaming
        )
        logging.info("Agente inicializado com sucesso.")

        # Executa o agente
        logging.info(f"Executando agente para input: '{input_text[:120]}'")
        response = agent_executor.invoke({'input': input_text})
        tempo_execucao = round(time.time() - inicio, 2)
        logging.info(f"Execução concluída em {tempo_execucao}s")

        # Salva memória
        logging.info("Salvando memória da conversa...")
        save_chat_history(session_id, memory)

        final_text = handler.get_response() if streaming else response.get("output", "")
        logging.debug(f"Resposta gerada pelo agente (resumida): {final_text[:200]}")

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

        # Verificação do uso de tools
        if response.get("intermediate_steps"):
            step = response["intermediate_steps"][0]
            log_data["tool"] = step[0].tool
            log_data["tool_output"] = str(step[1])
            tool_respose = step[1].get("response", "")

            logging.info(f"Ferramenta utilizada: {log_data['tool']}")

            if "tokens_used" in step[1]:
                tool_tokens_used += step[1]["tokens_used"]
                logging.debug(f"Tokens usados pela ferramenta: {step[1]['tokens_used']}")

        # Tokens estimados
        logging.info("Calculando tokens estimados da requisição...")
        tokens_response = estimar_tokens_completos(
            system_prompt=system_prompt,
            chat_history=memory.chat_memory.messages,
            tools_json=tools_json,
            tool_response=tool_respose,
            tool_tokens_used=tool_tokens_used
        )
        logging.debug(f"Tokens estimados: {tokens_response}")

        log_data["tokens_estimados"] = tokens_response

        # Executa controle de uso em segundo plano
        logging.info("Enviando dados de uso de tokens para gerenciamento em background...")
        threading.Thread(
            target=menage_chat_usage,
            args=(business_id, "gpt-4o-mini", log_data),
            daemon=True
        ).start()

        logging.info("=== AgentAsk() finalizado com sucesso ===")
        return log_data

    except Exception as e:
        logging.exception(f"Erro durante execução do AgentAsk: {e}")

        return {
            "response": "Desculpa! Não foi possível responder a pergunta. Por favor tente novamente.",
            "session_id": session_id,
            "erro": str(e),
            "status": "error",
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
