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

class VectorStoreRetriver(Toolkit):
    """
    VectorStoreRetriver is a toolkit for (RAG) retrieval augmented generation. 

    Args:
        enable_context_generation (bool): Enable generate context functionality. Default is True.
        all (bool): Enable all tools. Overrides individual flags when True. Default is False.
    """

    def __init__(
        self,
        response_collector: Any,
        enable_context_generation: bool = True,
        all: bool = False,
        **kwargs,
    ):
        self.response_collector = response_collector
        tools: List[Any] = []

        if all or enable_context_generation:
            tools.append(self.context_generation)

        super().__init__(name="vector_store_tools", tools=tools, **kwargs)

    def context_generation(self, query: str) -> str:
        """
        Generate contextual information based on a user query.
        """
        try:
            context = CONTEXT
            self.response_collector.add_metadata(
                tool_name="context_generation",
                payload={
                    "context": len(context)
                }
            )

        except Exception as e:
            return f"Failed to generate context: {str(e)}"

        return context



################################################### BASE TOOL ###################################################
################################################### --------- ###################################################




class BaseAgentTools(Toolkit):
    """
    *BASIC_DESCRIPTION_OF_THE_TOOLS_GROUP* (BaseAgentTools is a toolkit for writing blogs.)

    Args:
        parm_example (str): Set the blog text style. Default is "journalistic".
        enable_example_tool (bool): Enable example tool functionality. Default is True.
        all (bool): Enable all tools. Overrides individual flags when True. Default is False.
    """

    def __init__(
        self,
        parm_example: str = "journalistic",
        enable_example_tool: bool = True,
        all: bool = False,
        response_collector: Any = None,
        **kwargs,
    ):
        self.response_collector = response_collector
        tools: List[Any] = []

        if all or enable_example_tool:
            tools.append(self.example_tool)

        super().__init__(name="writing_blogs_tools", tools=tools, **kwargs)
    
    def _update_response(self, tool_name: str, payload: dict):
        """
        Internal helper method used to collect metadata about tool execution.
        """
        if self.response_collector:
            self.response_collector.add_metadata(
                tool_name=tool_name,
                payload=payload
            )

    def example_tool(self, parm: str) -> str:
        """
        *BASIC_DESCRIPTION_OF_THE_TOOL* (Example tool is a tool for writing blogs based on a user-provided theme.)

        Args:
            parm (str): Explain the parameter.

        Returns:
            str: The text of the blog or error message.
        """
        try:
            # In this example, the steps to write a blog are performed.
            blog_content = "The content of the blog"

            # Collect metadata
            self._update_response("example_tool", {"blog_content": blog_content})

        except Exception as e:
            return f"Failed to generate blog context: {str(e)}"

        return blog_content
    
    def example_tool2(self):
        # .......
        pass



