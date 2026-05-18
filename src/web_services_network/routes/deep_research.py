import os

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from typing import Optional, List
from pydantic import BaseModel

from src.web_services_network.request_resource import RequestResorse, Authorization

from src.deep_research.tavily_research.tavily_core import TavilyDeepResearch
from src.deep_research.tavily_research.context_builder import TavilyContextBuilder, TavilyResearchRunner

router = APIRouter(
    prefix="/deep-research",
    tags=["deep-research"]
)

load_dotenv()

class ContextBuilderRequest(BaseModel):
    query: str
    search_depth: str = "advanced"
    max_results: int = 35
    topic: str = "general"
    include_answer: bool = True
    min_score: float = 0.5


@router.post("/context-builder",
    summary="Builds context for deep research using TavilyDeepResearch.",
    #dependencies=[Depends(Authorization.validate_api_key)]
)
def context_builder(payload: ContextBuilderRequest):
    try:
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

        return {
            "status": 200,
            "query": payload.query,
            "result": markdown_context
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

