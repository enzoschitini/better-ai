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

# payload estruturado
payload = ContextBuilderRequest(
    query="Latest developments in data science"
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

print(markdown_context)

# python -m src.agents.agent_flow.ds