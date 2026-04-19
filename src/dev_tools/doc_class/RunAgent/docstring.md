```python
import json
from pydantic import BaseModel
from dotenv import load_dotenv

from agno.agent import Agent
from agno.os import AgentOS
from agno.models.groq import Groq

from src.agents.utils.tool_response import ToolResponse
from src.agents.utils.test_agents.format_response import FormatAgentResponse

load_dotenv()

class RunAgent:
    """
    Class to manage and run agent operations including debugging, generating JSON responses, 
    and serving the agent via an OS app interface. Provides methods to interact with the agent
    and handle its output in different formats.

    Args: 
    :param agent (Agent): The agent instance to be managed and run.

    Methods:
            debug(): Prints the agent's response to a given input string.
            js_reponse(): Runs the agent with an input string and outputs the response formatted as JSON, optionally saving to a file and printing tool metadata.
            agent_os(): Sets up and serves the agent using AgentOS with configurable server parameters.
    """
    def __init__(self, agent: Agent):
        self.agent = agent

    def debug(self, ask: str = "Hello!"):
        self.agent.print_response(ask)

    def js_reponse(self, ask: str = "Hello!", path: str = None, tool_response: ToolResponse = None):
        """
        Runs the agent with the specified input string and returns a formatted JSON response.
        Optionally saves the response to a JSON file and prints additional tool metadata if provided.

        Args: 
            ask (str): The input text to send to the agent. Default is "Hello!".
            path (str): The directory path where the JSON response file will be saved. Default is None, which uses "src/agents".
            tool_response (ToolResponse): Optional tool response to print metadata from. Default is None.

        Returns:
            dict: The agent's response formatted as a dictionary ready for JSON serialization.
        """
        class AgentInput(BaseModel):
            text: str

        response = self.agent.run(
            input=AgentInput(text=ask),
            stream=False,
        )

        formatter = FormatAgentResponse(response)
        formated_response = formatter.format()

        path = path or "src/agents"
        formatter.save_json(formated_response, f"{path}/agent_response.json")

        print(json.dumps(formated_response, indent=2))

        if tool_response:
            print(f"\nTool Responses:\n{tool_response.get_metadata()}")
        
        print(f'\nResponse: {formated_response["content"]}')
        return formated_response

    def agent_os(
        self,
        id: str = "my_agent",
        name: str = "My Agent",
        description: str = "An agent created for demonstration purposes.",
        host: str = "localhost",
        port: int = 7777,
    ):
        """
        Initializes and serves the agent via an AgentOS application with configurable ID, 
        name, description, and server host and port.

        Args: 
            id (str): Unique identifier for the agent. Default is "my_agent".
            name (str): Display name for the agent. Default is "My Agent".
            description (str): Description of the agent's purpose. Default is "An agent created for demonstration purposes.".
            host (str): Host address for serving the agent app. Default is "localhost".
            port (int): Port number for the agent app server. Default is 7777.
        """
        agent_os = AgentOS(
            id=id,
            name=name,
            description=description,
            agents=[self.agent],
        )

        app = agent_os.get_app()
        agent_os.serve(app=app, host=host, port=port)

if __name__ == "__main__":
    agent = Agent(
        model=Groq(id="llama-3.3-70b-versatile"),
        debug_level=True,
    )

    runner = RunAgent(agent=agent)
    response = runner.debug()
```