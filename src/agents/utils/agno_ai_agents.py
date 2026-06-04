from src.agents.utils.tool_response import ToolContext

class ToolContext:
    def __init__(self):
        self.tool_context = ToolContext()


class BaseAgent:
    def create_agent(self, metadata: dict, tool_context: ToolContext):
        raise NotImplementedError


class AgnoAiAgents:
    def __init__(self):
        self._registry = {}

    def register(self, name: str, agent_class):
        self._registry[name] = agent_class

    def create_agent(self, id: str, metadata: dict):
        if id not in self._registry:
            raise ValueError(f"Agent '{id}' não registrado.")

        tool_context = ToolContext()

        agent_instance = self._registry[id]()
        agent = agent_instance.create_agent(metadata, tool_context)

        return agent, tool_context


# python -m src.agents.utils.agno_ai_agents