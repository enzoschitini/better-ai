import random

from dotenv import load_dotenv
from typing import List, Any
from datetime import datetime
from pydantic import BaseModel

from agno.tools import Toolkit
from src.agents.utils.tool_response import ToolResponse

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

class TrendRadarToolkit(Toolkit):
    """
    TrendRadarToolkit is a web search toolkit for retrieving current trends on any topic.

    Uses Tavily's deep research engine to search the web and return up-to-date
    trend information as structured Markdown content with source references.

    Args:
        enable_get_trends (bool): Enable the web trend search tool. Default is True.
        all (bool): Enable all tools. Overrides individual flags when True. Default is False.
        TOOL_RESPONSER (ToolResponse): Optional metadata collector for tracking tool calls. Default is None.
    """
    def __init__(
        self,
        enable_get_trends: bool = True,
        all: bool = False,
        TOOL_RESPONSER: ToolResponse = None,
        **kwargs,
    ):
        self.TOOL_RESPONSER = TOOL_RESPONSER
        tools: List[Any] = []

        if all or enable_get_trends:
            tools.append(self.get_trends)

        super().__init__(name="base_toolkit", tools=tools, **kwargs)

    def _update_response(self, tool_name: str, payload: dict):
        """
        Internal helper to collect metadata about tool execution.
        """
        if self.TOOL_RESPONSER:
            self.TOOL_RESPONSER.add_metadata(
                tool_name=tool_name,
                payload=payload
            )

    def get_trends(self, query: str) -> str:
        """
        Searches the web for current trends related to a given query.

        Performs a deep web search using Tavily to retrieve up-to-date trend
        information on the specified topic. Results are returned as a formatted
        Markdown string containing summarized content and source references.
        If the query is empty or contains only whitespace, the search is aborted
        and an error message is returned.

        Args:
            query (str):
                The topic or keyword to search trends for.
                Must be a non-empty string with at least one non-whitespace character.

        Returns:
            str: A Markdown-formatted string summarizing current web trends related
                to the query, prefixed with a contextual label. Returns an error
                message string if the query is invalid or if the search fails.

        Notes:
            - Search is performed with advanced depth and up to 15 results by default.
            - Only sources with a relevance score above 0.5 are included in the output.
            - Collected source URLs and the original query are forwarded to the
              TOOL_RESPONSER metadata collector, if one was provided at initialization.
        """
        try:
            if not query or not query.strip():
                return "A valid query is required."

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

            self._update_response(
                "get_trends",
                {"query": query, "urls": urls}
            )

        except Exception as e:
            return f"Failed to get trends: {str(e)}"

        return f"Current trends related to '{query}': {markdown_context}."

if __name__ == "__main__":
    toolkit = TrendRadarToolkit()

    trends_result = toolkit.get_trends("What are the current trends in technology?")
    print(f"{trends_result}\n")


# python -m src.agents.trend_radar.tools.toolkit