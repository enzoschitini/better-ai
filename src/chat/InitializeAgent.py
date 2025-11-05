# =========================================
# IMPORTS
# =========================================
import uuid
import requests
from dotenv import load_dotenv

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

# Ou apenas warnings específicos de UserWarning
warnings.filterwarnings("ignore", category=UserWarning)

load_dotenv()

# =========================================
# STREAM HANDLER
# =========================================
class StreamHandler(BaseCallbackHandler):
    """Exibe tokens em tempo real durante a geração."""
    def __init__(self):
        self.full_response = ""

    def on_llm_new_token(self, token: str, **kwargs):
        #print(token, end="", flush=True)
        self.full_response += token

    def get_response(self):
        return self.full_response

# =========================================
# INICIALIZAÇÃO DO AGENTE
# =========================================
def initialize_agent(session_id, user_prompt, temperature, tools, tools_json, tool_run, streaming=False):
    session_id = session_id or str(uuid.uuid4())
    memory = create_memory(session_id)
    handler = StreamHandler() if streaming else None
    
    chat = ChatOpenAI(
        temperature=temperature,
        streaming=streaming,
        callbacks=[handler] if streaming else None,
    )

    #system_prompt = f"{prompt}\n{chat_system_prompt(system_prompt_type)}"
    system_prompt = f"{user_prompt}\n{chat_system_prompt("standard")}"

    prompt = ChatPromptTemplate.from_messages([
        ('system', system_prompt),
        MessagesPlaceholder(variable_name='chat_history'),
        ('user', '{input}'),
        MessagesPlaceholder(variable_name='agent_scratchpad')
    ])

    pass_through = RunnablePassthrough.assign(
        agent_scratchpad=lambda x: format_to_openai_function_messages(x['intermediate_steps'])
    )

    agent_chain = (
        pass_through
        | prompt
        | chat.bind(functions=tools_json)
        | OpenAIFunctionsAgentOutputParser()
    )

    agent_executor = AgentExecutor(
        agent=agent_chain,
        tools=tools,
        memory=memory,
        verbose=False,
        return_intermediate_steps=True
    )

    return agent_executor, memory, session_id, handler, system_prompt