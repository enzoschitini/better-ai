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
        resource = RequestResorse()
        researcher = TavilyDeepResearch()

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

        return resource.success_response(markdown_context)

    except Exception as e:
        return resource.error_response(e)

"""
curl --location 'http://127.0.0.1:8000/deep-research/context-builder' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer betterai-dev-96d97aa3-492d-4ecc-9ced-3dc34c0cf062-945d3391-85dc-4a19-a054-191d048b62c0' \
--header 'Client: BETTERAI' \
--header 'SecretKey: Bearer betterai-dev-6c6febc5-de97-464a-929b-cce1b2278de1' \
--data '{
    "query": "Quais as principais tendências de IA em 2026?",
    "search_depth": "advanced",
    "max_results": 2,
    "topic": "general",
    "include_answer": true,
    "min_score": 0.5
  }'
"""

