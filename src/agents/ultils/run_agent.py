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

    def run_agent(self, ask: str = "Hello!", path: str = None, tool_responses = None):
        class AgentInput(BaseModel):
            text: str

        response = self.agent.run(
            input=AgentInput(text=ask)
        )

        formatter = FormatAgentResponse(response)
        formated_response = formatter.format()

        if path:
            formatter.save_json(formated_response, f"{path}agent_response.json")

        print(json.dumps(formated_response, indent=2))

        if tool_responses:
            print(f"\nTool Responses:\n{tool_responses.get_metadata()}")
        
        print(f"\nResponse: {formated_response["content"]}")
        return formated_response

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

