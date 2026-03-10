import json
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from src.agents.agent_flow.format_response import FormatAgentResponse

from agno.agent import Agent
from agno.os import AgentOS

from agno.db.sqlite import SqliteDb
from agno.memory.manager import MemoryManager

from agno.models.groq import Groq
from agno.models.openai import OpenAIChat

from agno.tools.yfinance import YFinanceTools

load_dotenv()

"""
Prende in considerazione un insieme di messaggi
"""

BASE_PATH = "src/agents/agent_flow/"
# Setup your database
db = SqliteDb(db_file=f"{BASE_PATH}agno.db")

prompt = {
    "instructions": """
Você é um analista e tem diferentes clientes. Lembre-se de cada cliente, suas informações e preferências.
""",

    "description": """
Você é um assistente inteligente.
Use ferramentas apenas quando a pergunta exigir informações atuais ou dados externos.
Para perguntas de conhecimento geral, responda diretamente com base no seu conhecimento interno.
Não peça contexto adicional se a pergunta for clara.
""",

    "memory_manager_instructions": """
Não armazene CPF e senhas dos usuários
"""
}

agent = Agent(
    # Menage sessions and users
    session_id="session_4",
    user_id="user_2",

    # Models: OpenAIChat(id="gpt-4.1-mini"), Groq(id="llama-3.3-70b-versatile"),
    model=Groq(id="llama-3.3-70b-versatile", temperature=0.8), 

    instructions=prompt["instructions"],
    description=prompt["description"],
    #debug_mode=True,
    stream=False,
    #markdown=True,

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

class AgentInput(BaseModel):
    text: str

response = agent.run(
    input=AgentInput(text="Ciao! Mi chiamo Enzo!")
)

formatter = FormatAgentResponse(response)
super_json = formatter.format()
formatter.save_json(super_json, "src/agents/agent_flow/agent_response.json")

print(f"\n\n{json.dumps(super_json, indent=2)}\n\n")

# python -m src.agents.agent_flow.agent

#agent.print_response("Qual è il mio nome?")
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

"""
if __name__ == "__main__":
    class AgentInput(BaseModel):
        text: str

    response = agent.run(
        input=AgentInput(text="Ciao! Mi chiamo Enzo!")
    )
    agent_os = AgentOS(
        id="my-first-os",
        description="My first AgentOS",
        agents=[agent],
    )

    app = agent_os.get_app()

    # Default port is 7777, change with port=... http://localhost:7777
    #agent_os.serve(app="src.agents.agent_flow.agent:app", reload=True)
    agent_os.serve(app=app)
#"""

"""
# RUN + AgentOS

from fastapi import FastAPI
from pydantic import BaseModel

class AgentInput(BaseModel):
    text: str

@app.post("/test-run")
def test_run(data: AgentInput):
    response = agent.run(input=data.text)

    return {
        "content": response.content,
        "metrics": response.metrics,
        "tools": response.tools,
        "memory": response.memory,
    }
"""








# https://github.com/enzoschitini/Asimov-Academy/tree/asimov-academy/lessons/ai_engineering/4.%20Criando%20Agentes%20de%20IA%20com%20Agno/04_storage_memory
