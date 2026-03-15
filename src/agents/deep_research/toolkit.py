import os
from dotenv import load_dotenv
from typing import Any, List
from pydantic import BaseModel

from agno.tools import Toolkit

# Deep Research Packages
from src.deep_research.tavily_research.tavily_core import TavilyDeepResearch
from src.deep_research.tavily_research.context_builder import TavilyContextBuilder, TavilyResearchRunner

load_dotenv()

class ContextBuilderRequest(BaseModel):
    query: str
    search_depth: str = "advanced"
    max_results: int = 15
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
        TOOL_RESPONSER: Any = None,
        **kwargs,
    ):
        self.TOOL_RESPONSER = TOOL_RESPONSER
        tools: List[Any] = []

        if all or enable_web_research:
            tools.append(self.web_research)

        super().__init__(name="deep_research_tools", tools=tools, **kwargs)
    
    def _update_response(self, tool_name: str, payload: dict):
        """
        Internal helper method used to collect metadata about tool execution.
        """
        if self.TOOL_RESPONSER:
            self.TOOL_RESPONSER.add_metadata(
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

            researcher = TavilyDeepResearch()

            builder = TavilyContextBuilder(
                researcher=researcher,
                min_score=payload.min_score
            )

            runner = TavilyResearchRunner(builder)

            context = runner.run(
                query=payload.query,
                search_depth=payload.search_depth,
                max_results=payload.max_results,
                topic=payload.topic,
                include_answer=payload.include_answer
            )

            markdown_context = context["markdown"]
            urls = context["urls"]

            # Collect metadata
            self._update_response("web_research", {"urls": urls, "markdown_context_size": len(markdown_context)})

        except Exception as e:
            return f"Failed to generate context of research: {str(e)}"

        return markdown_context


# python -m src.agents.deep_research.toolkit