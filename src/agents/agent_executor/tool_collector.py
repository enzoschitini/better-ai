import json
from typing import Any, Dict, Optional


class ToolCollector:
    """Collects tool metadata from the shared ToolResponse context."""

    def __init__(self, tool_context: Optional[Any] = None):
        self._tool_context = tool_context

    def collect(self) -> Dict[str, Any]:
        if self._tool_context is None:
            return {}
        return self._tool_context.get_metadata() or {}

    def clear(self) -> None:
        if self._tool_context is not None:
            self._tool_context.clear_metadata()

    def collect_as_json(self, ensure_ascii: bool = False) -> str:
        return json.dumps(self.collect(), indent=2, ensure_ascii=ensure_ascii)
