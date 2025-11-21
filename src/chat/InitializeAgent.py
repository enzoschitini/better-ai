# =========================================
# IMPORTS
# =========================================
import uuid
import requests
from dotenv import load_dotenv
import logging

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.schema.runnable import RunnablePassthrough
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents import AgentExecutor
from langchain.callbacks.base import BaseCallbackHandler

from src.chat.buffer_memory import create_memory
from src.chat.prompts.prompt_template import chat_system_prompt
import warnings

# Ignora todos os warnings
warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", category=UserWarning)

load_dotenv()

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(filename)s - line: %(lineno)d - %(levelname)s - %(message)s'
)

# =========================================
# STREAM HANDLER
# =========================================
class StreamHandler(BaseCallbackHandler):
    """Exibe tokens em tempo real durante a geração."""
    def __init__(self):
        self.full_response = ""

    def on_llm_new_token(self, token: str, **kwargs):
        self.full_response += token

    def get_response(self):
        return self.full_response


# =========================================
# INICIALIZAÇÃO DO AGENTE (COM LOGS)
# =========================================
def initialize_agent(session_id, user_prompt, temperature, tools, tools_json, tool_run, streaming=False):
    logging.info("🟢 initialize_agent chamado")

    try:
        # ===== SESSION ID =====
        if not session_id:
            session_id = str(uuid.uuid4())
            logging.info(f"Nenhum session_id recebido. Gerado novo: {session_id}")
        else:
            logging.info(f"Utilizando session_id existente: {session_id}")

        # ===== MEMORY =====
        logging.debug("Carregando memória da sessão...")
        memory = create_memory(session_id)
        logging.info(f"Memória carregada para sessão {session_id}. "
                     f"{len(memory.chat_memory.messages)} mensagens restauradas.")

        # ===== STREAM HANDLER =====
        handler = StreamHandler() if streaming else None
        if streaming:
            logging.debug("Streaming ativado. StreamHandler inicializado.")
        else:
            logging.debug("Streaming desativado.")

        # ===== OPENAI CHAT MODEL =====
        logging.debug("Inicializando ChatOpenAI...")
        chat = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=temperature,
            streaming=streaming,
            callbacks=[handler] if streaming else None,
        )
        logging.info(f"Modelo OpenAI iniciado com temperature={temperature}")

        # ===== SYSTEM PROMPT =====
        system_prompt = f"{user_prompt}\n{chat_system_prompt('standard')}"
        logging.debug(f"System prompt criado: {system_prompt[:80]}...")

        # ===== PROMPT TEMPLATE =====
        prompt = ChatPromptTemplate.from_messages([
            ('system', system_prompt),
            MessagesPlaceholder(variable_name='chat_history'),
            ('user', '{input}'),
            MessagesPlaceholder(variable_name='agent_scratchpad')
        ])

        # ===== RUNNABLE WRAPPER =====
        pass_through = RunnablePassthrough.assign(
            agent_scratchpad=lambda x: format_to_openai_function_messages(x['intermediate_steps'])
        )

        # ===== AGENT CHAIN =====
        agent_chain = (
            pass_through
            | prompt
            | chat.bind(functions=tools_json)
            | OpenAIFunctionsAgentOutputParser()
        )
        logging.info("Agent Chain montado com sucesso.")

        # ===== EXECUTOR FINAL =====
        agent_executor = AgentExecutor(
            agent=agent_chain,
            tools=tools,
            memory=memory,
            verbose=False,
            return_intermediate_steps=True
        )

        logging.info("Agent Executor criado e pronto para uso.")

        return agent_executor, memory, session_id, handler, system_prompt

    except Exception as e:
        logging.error(f"❌ Erro ao inicializar o agente: {e}", exc_info=True)
        raise
