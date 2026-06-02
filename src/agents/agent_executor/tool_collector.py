import json
from typing import Any, Dict, Optional


class ToolCollector:
    """Collects tool metadata from the shared ToolResponse context."""

    def __init__(self, tool_responser: Optional[Any] = None):
        self._tool_responser = tool_responser

    def collect(self) -> Dict[str, Any]:
        if self._tool_responser is None:
            return {}
        return self._tool_responser.get_metadata() or {}

    def clear(self) -> None:
        if self._tool_responser is not None:
            self._tool_responser.clear_metadata()

    def collect_as_json(self, ensure_ascii: bool = False) -> str:
        return json.dumps(self.collect(), indent=2, ensure_ascii=ensure_ascii)
