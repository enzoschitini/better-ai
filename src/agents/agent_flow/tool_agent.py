import json
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from src.agents.agent_flow.format_response import FormatAgentResponse

from agno.agent import Agent

from agno.models.groq import Groq
from agno.models.openai import OpenAIChat

from agno.tools.yfinance import YFinanceTools

load_dotenv()

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

finance = YFinanceTools()

agent = Agent(
    # Models: OpenAIChat(id="gpt-4.1-mini"), Groq(id="llama-3.3-70b-versatile"),
    model=Groq(id="llama-3.3-70b-versatile", temperature=0.8), 

    instructions=prompt["instructions"],
    description=prompt["description"],
    debug_level=True,
    tools=[finance],
)

ASK = "Qual é a cotação da petrobras?"

agent.print_response(ASK)

class AgentInput(BaseModel):
    text: str

response = agent.run(
    input=AgentInput(text=ASK)
)

formatter = FormatAgentResponse(response)
super_json = formatter.format()
formatter.save_json(super_json, "src/agents/agent_flow/agent_response.json")

print(f"\n\n{json.dumps(super_json, indent=2)}\n\n")

print(f"Metadata: {finance.response_metadata()}")

# python -m src.agents.agent_flow.tool_agent

"""
agent.print_response("Qual é a cotação da petrobras?")
#agent.print_response("Qual é a cotação da petrobras?", session_id="session_1", user_id="petrobras")
agent.print_response("Qual é a cotação da vale?")
agent.print_response("Quais empresas já consultamos a cotação?")
"""
