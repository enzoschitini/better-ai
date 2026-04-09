import os
from dotenv import load_dotenv

#os.environ["AGNO_TELEMETRY"] = "false"
#AGNO_TELEMETRY = os.getenv("AGNO_TELEMETRY")

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.tavily import TavilyTools
from agno.os import AgentOS

load_dotenv()

assistant = Agent(
    name="Assistant",
    model=OpenAIChat(id="gpt-4.1-mini"),
    tools=[TavilyTools()],
    description=(
        "Você é um assistente inteligente. "
        "Use ferramentas apenas quando a pergunta exigir informações atuais "
        "ou dados externos. "
        "Para perguntas de conhecimento geral, responda diretamente com base "
        "no seu conhecimento interno. "
        "Não peça contexto adicional se a pergunta for clara."
    ),
    debug_mode=True,
    stream=False,
    markdown=True,
)

agent_os = AgentOS(
    id="my-first-os",
    description="My first AgentOS",
    agents=[assistant],
)

app = agent_os.get_app()

if __name__ == "__main__":
    # Default port is 7777, change with port=...
    print("\n\n--------- New call ---------\n\n")
    agent_os.serve(app="minimal_setup:app", reload=True)
