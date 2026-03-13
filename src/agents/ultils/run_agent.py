import json
from pydantic import BaseModel
from dotenv import load_dotenv

from agno.agent import Agent
from agno.os import AgentOS
from agno.models.groq import Groq

from src.agents.ultils.format_response import FormatAgentResponse

load_dotenv()

class RunAgent:
    def __init__(self, agent):
        self.agent = agent

    def debug(self, ask: str = "Hello!"):
        self.agent.print_response(ask)

    def process(self, ask: str = "Hello!"):
        class AgentInput(BaseModel):
            text: str

        response = self.agent.run(
            input=AgentInput(text=ask)
        )

        return response

    def agent_os(self):
        agent_os = AgentOS(
            id="my-first-os",
            description="My first AgentOS",
            agents=[self.agent],
        )

        app = agent_os.get_app()
        agent_os.serve(app=app)

if __name__ == "__main__":
    agent = Agent(
        model=Groq(id="llama-3.3-70b-versatile"),
        debug_level=True,
    )

    runner = RunAgent(agent=agent)
    response = runner.process()

    response = runner.agent_os()

# python -m src.agents.ultils.run_agent

