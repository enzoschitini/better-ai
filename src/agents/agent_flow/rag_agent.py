import json
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from src.agents.agent_flow.format_response import FormatAgentResponse
from src.agents.agent_flow.config import CONTEXT

from agno.agent import Agent
from agno.os import AgentOS

from agno.models.groq import Groq
from agno.models.openai import OpenAIChat

load_dotenv()

prompt = {
    "instructions": """
Você é um agente de IA especializado em análise e recuperação de informações.

Você possui acesso a ferramentas capazes de buscar informações em uma base de conhecimento
(vector store). Utilize essas ferramentas sempre que precisar de informações externas
ou quando a pergunta do usuário depender de conhecimento específico.

Diretrizes de comportamento:

1. Quando a pergunta exigir conhecimento factual, técnico ou específico,
   utilize a ferramenta de recuperação de contexto antes de responder.

2. Após obter o contexto da ferramenta, analise cuidadosamente as informações
   retornadas e utilize apenas os dados relevantes para formular sua resposta.

3. Priorize sempre as informações vindas da base de conhecimento recuperada.

4. Se o contexto recuperado não for suficiente para responder com segurança,
   informe ao usuário que a informação disponível é limitada.

5. Evite inventar fatos que não estejam presentes no contexto ou que não sejam
   amplamente conhecidos.

6. Sempre produza respostas claras, estruturadas e objetivas.

7. Caso a pergunta seja simples e não dependa de informações externas,
   responda diretamente sem utilizar ferramentas.
""",

    "description": """
Você é um agente de IA baseado em Retrieval Augmented Generation (RAG).

Seu papel é auxiliar usuários respondendo perguntas com base em informações
recuperadas de uma base de conhecimento vetorial (vector store). Para isso,
você pode utilizar ferramentas que buscam documentos relevantes, analisá-los
e gerar respostas fundamentadas.

O agente deve combinar raciocínio próprio com o contexto recuperado para
produzir respostas precisas, confiáveis e bem explicadas.
""",

    "memory_manager_instructions": """
Gerencie memória de forma responsável.

Boas práticas:
- Armazene preferências do usuário, contexto da conversa e informações úteis
  para melhorar interações futuras.
- Não armazene informações sensíveis como CPF, senhas, números de cartão,
  dados bancários ou qualquer informação pessoal crítica.
- Caso o usuário forneça esse tipo de informação, ignore-a para fins de memória.
"""
}

class ToolResponse:
    def __init__(self, metadata=None):
        self.metadata = metadata or {}

    def add_metadata(self, tool_name: str, payload: dict):
        self.metadata[tool_name] = payload
    
    def get_metadata(self):
        return self.metadata



from typing import Any, List
from agno.tools import Toolkit

class VectorStoreRetriver(Toolkit):
    """
    VectorStoreRetriver is a toolkit for (RAG) retrieval augmented generation. 

    Args:
        enable_context_generation (bool): Enable generate context functionality. Default is True.
        all (bool): Enable all tools. Overrides individual flags when True. Default is False.
    """

    def __init__(
        self,
        response_collector: Any,
        enable_context_generation: bool = True,
        all: bool = False,
        **kwargs,
    ):
        self.response_collector = response_collector
        tools: List[Any] = []

        if all or enable_context_generation:
            tools.append(self.context_generation)

        super().__init__(name="vector_store_tools", tools=tools, **kwargs)

    def context_generation(self, query: str) -> str:
        """
        Generate contextual information based on a user query.
        """

        try:
            context = CONTEXT
            self.response_collector.add_metadata(
                tool_name="VectorStoreRetriver",
                payload={
                    "context": len(context)
                }
            )

        except Exception as e:
            return f"Failed to generate context: {str(e)}"

        return context

response_collector = ToolResponse()

agent = Agent(
    # Models: OpenAIChat(id="gpt-4.1-mini"), Groq(id="llama-3.3-70b-versatile"),
    model=OpenAIChat(id="gpt-4.1-mini"), 

    instructions=prompt["instructions"],
    description=prompt["description"],
    debug_level=True,
    tools=[
        VectorStoreRetriver(response_collector)
    ],
)

ASK = "Resuma os documentos da base"
#agent.print_response(ASK)

class AgentInput(BaseModel):
    text: str

response = agent.run(
    input=AgentInput(text=ASK)
)

formatter = FormatAgentResponse(response)
super_json = formatter.format()
formatter.save_json(super_json, "src/agents/agent_flow/agent_response.json")

print(f"\n\n{json.dumps(super_json, indent=2)}\n\n")

print(f"Metadata: {response_collector.get_metadata()}")

"""
if __name__ == "__main__":
    agent_os = AgentOS(
        id="my-first-os",
        description="My first AgentOS",
        agents=[agent],
    )

    app = agent_os.get_app()
    agent_os.serve(app=app)

"""

# python -m src.agents.agent_flow.rag_agent
