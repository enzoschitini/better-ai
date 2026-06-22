from typing import Any, Dict, Tuple, Type


class LocalToolResponse:
    """Standalone tool metadata collector used by /agent_executor flow."""

    def __init__(self, metadata: Dict[str, Any] | None = None):
        self.metadata = metadata or {}

    def add_metadata(self, tool_name: str, payload: Dict[str, Any]) -> None:
        self.metadata[tool_name] = payload

    def get_metadata(self) -> Dict[str, Any]:
        return self.metadata

    def clear_metadata(self) -> None:
        self.metadata = {}


class LocalToolContext:
    def __init__(self):
        self.tool_context = LocalToolResponse()


class LocalAgentFactory:
    """Minimal local registry/factory for standalone executor flow."""

    def __init__(self):
        self._registry: Dict[str, Type] = {}

    def register(self, name: str, agent_class: Type) -> None:
        self._registry[name] = agent_class

    def create_agent(self, name: str, metadata: Dict[str, Any]) -> Tuple[Any, LocalToolContext]:
        if name not in self._registry:
            raise ValueError(f"Agent '{name}' not registered.")

        tool_context = LocalToolContext()
        agent_instance = self._registry[name]()
        agent = agent_instance.create_agent(metadata, tool_context)
        return agent, tool_context
