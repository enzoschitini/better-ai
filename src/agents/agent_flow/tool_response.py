


class ToolResponse:
    def __init__(self, metadata=None):
        self.metadata = metadata or {}

    def add_metadata(self, tool_name: str, payload: dict):
        self.metadata[tool_name] = payload
    
    def get_metadata(self):
        return self.metadata

tool_responser = ToolResponse()

tool_responser.add_metadata(
    tool_name="deep_research",
    payload={
        "site": "https://example.com"
    }
)

tool_responser.add_metadata(
    tool_name="image_generation",
    payload={
        "image_size": "4k"
    }
)

response = tool_responser.get_metadata()
print(response)


