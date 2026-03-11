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







import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Deep Research Packages
from src.deep_research.tavily_research.tavily_core import TavilyDeepResearch
from src.deep_research.tavily_research.context_builder import TavilyContextBuilder, TavilyResearchRunner

load_dotenv()

class ContextBuilderRequest(BaseModel):
    query: str
    search_depth: str = "advanced"
    max_results: int = 35
    topic: str = "general"
    include_answer: bool = True
    min_score: float = 0.5

class DeepResearch(Toolkit):
    """
    DeepResearch is a toolkit for deep web searches.

    Args:
        enable_web_research (bool): Enable web research functionality. Default is True.
        all (bool): Enable all tools. Overrides individual flags when True. Default is False.
    """

    def __init__(
        self,
        enable_web_research: bool = True,
        all: bool = False,
        response_collector: Any = None,
        **kwargs,
    ):
        self.response_collector = response_collector
        tools: List[Any] = []

        if all or enable_web_research:
            tools.append(self.web_research)

        super().__init__(name="deep_research_tools", tools=tools, **kwargs)
    
    def _update_response(self, tool_name: str, payload: dict):
        """
        Internal helper method used to collect metadata about tool execution.
        """
        if self.response_collector:
            self.response_collector.add_metadata(
                tool_name=tool_name,
                payload=payload
            )

    def web_research(self, query: str) -> str:
        """
        web_research is a tool for deep web searches based on a user-provided query.)

        Args:
            query (str): The user's search query.

        Returns:
            str: A context of deep research or error message.
        """
        try:
            payload = ContextBuilderRequest(
                query=query
            )

            researcher = TavilyDeepResearch(
                api_key=os.getenv("TAVILY_API_KEY")
            )

            builder = TavilyContextBuilder(
                researcher=researcher,
                min_score=payload.min_score
            )

            runner = TavilyResearchRunner(builder)

            markdown_context = runner.run(
                query=payload.query,
                search_depth=payload.search_depth,
                max_results=payload.max_results,
                topic=payload.topic,
                include_answer=payload.include_answer
            )

            # Collect metadata
            self._update_response("web_research", {"markdown_context": len(markdown_context)})

        except Exception as e:
            return f"Failed to generate context of research: {str(e)}"

        return markdown_context


# python -m src.agents.agent_flow.agent_toolkit


















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



