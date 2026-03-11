import json
from pydantic import BaseModel

from agno.os import AgentOS
from src.agents.agent_flow.format_response import FormatAgentResponse

class RunAgent:
    def __init__(self, agent):
        self.agent = agent

    def debug(self, ask: str = "Hello!"):
        self.agent.print_response(ask)

    def process(self, response_collector, ask: str = "Hello!"):
        class AgentInput(BaseModel):
            text: str

        response = self.agent.run(
            input=AgentInput(text=ask)
        )

        formatter = FormatAgentResponse(response)
        super_json = formatter.format()
        formatter.save_json(super_json, "src/agents/ultils/agent_response.json")

        print(f"\n\n{json.dumps(super_json, indent=2)}\n\n")

        print(f"Metadata: {response_collector.get_metadata()}")
        print(f"Response: {response.content}")

    def agent_os(self):
        agent_os = AgentOS(
            id="my-first-os",
            description="My first AgentOS",
            agents=[self.agent],
        )

        app = agent_os.get_app()
        agent_os.serve(app=app)
