from typing import Any, List
from agno.tools import Toolkit
from src.agents.agent_flow.config import CONTEXT

class ToolResponse:
    def __init__(self, metadata=None):
        self.metadata = metadata or {}

    def add_metadata(self, tool_name: str, payload: dict):
        self.metadata[tool_name] = payload
    
    def get_metadata(self):
        return self.metadata

# python -m src.agents.ultils.tool_response