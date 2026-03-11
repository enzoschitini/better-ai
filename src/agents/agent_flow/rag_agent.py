import json
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from src.agents.agent_flow.format_response import FormatAgentResponse
from src.agents.agent_flow.vector_store_tool import VectorStoreRetriver, ToolResponse
from src.agents.agent_flow.config import PROMPT

from agno.agent import Agent
from agno.os import AgentOS

from agno.models.groq import Groq
from agno.models.openai import OpenAIChat

load_dotenv()

response_collector = ToolResponse()

agent = Agent(
    model=OpenAIChat(id="gpt-4.1-mini"), 
    instructions=PROMPT["instructions"],
    description=PROMPT["description"],
    debug_level=True,
    tools=[VectorStoreRetriver(response_collector)],
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
