
class ToolResponse:
    def __init__(self, metadata=None):
        self.metadata = metadata or {}

    def add_metadata(self, tool_name: str, payload: dict):
        self.metadata[tool_name] = payload
    
    def get_metadata(self):
        return self.metadata
    
    def clear_metadata(self):
        self.metadata = {}

# python -m src.agents.utils.tool_response