from agno.agent import Agent

from agno.db.sqlite import SqliteDb
from agno.memory.manager import MemoryManager

from agno.models.groq import Groq
from agno.models.openai import OpenAIChat

from agno.tools.yfinance import YFinanceTools

from dotenv import load_dotenv

load_dotenv()

"""
Prende in considerazione un insieme di messaggi
"""

# Setup your database
db = SqliteDb(db_file="src/agents/agent_flow/agno.db")

prompt = {
    "instructions": """
Você é um analista e tem diferentes clientes. Lembre-se de cada cliente, suas informações e preferências.
""",

    "memory_manager_instructions": """
Não armazene CPF e senhas dos usuários
"""
}

agent = Agent(
    # Menage sessions and users
    session_id="session_3",
    user_id="user_2",

    # Models: OpenAIChat(id="gpt-4.1-mini"), Groq(id="llama-3.3-70b-versatile"),
    model=Groq(id="llama-3.3-70b-versatile"), 

    instructions=prompt["instructions"],
    #description="xxxxxxxxxx",

    # Memory
    db=db,
    add_history_to_context=True,
    num_history_runs=10,
    enable_user_memories=True,
    add_memories_to_context=True,

    memory_manager=MemoryManager(
        db=db,
        model=OpenAIChat(id="gpt-4.1-mini"),
        additional_instructions=prompt["memory_manager_instructions"]
    ),
    enable_agentic_memory=True,

    #session_summary_manager=
    #tools=[YFinanceTools()],
)

agent.print_response("Qual è il mio nome?")
#agent.print_response("Ciao! Mi chiamo Enzo!")
#agent.print_response("Mi piace giocare a pallone")
#agent.print_response("Il mio cantante preferito è Laura Pausini")
#agent.print_response("Ho 21 anni")

"""
agent.print_response("Qual é a cotação da petrobras?")
#agent.print_response("Qual é a cotação da petrobras?", session_id="session_1", user_id="petrobras")
agent.print_response("Qual é a cotação da vale?")
agent.print_response("Quais empresas já consultamos a cotação?")
"""








# https://github.com/enzoschitini/Asimov-Academy/tree/asimov-academy/lessons/ai_engineering/4.%20Criando%20Agentes%20de%20IA%20com%20Agno/04_storage_memory
