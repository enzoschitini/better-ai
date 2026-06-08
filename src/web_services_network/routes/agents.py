import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, List
from pydantic import BaseModel

from src.agents.trend_radar.agent import BaseAgent
from src.agents.agent_executor import AgentExecutor

router = APIRouter(
    prefix="/agents",
    tags=["agents"]
)


class AgentStreamRequest(BaseModel):
    ask: str
    citys: List[str]
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    clear_tool_metadata: bool = False


@router.post(
    "/stream",
    summary="Execute the trend radar agent with streamed responses",
    description=(
        "Run the trend radar agent using a simple JSON body and receive events as a streaming response. "
        "Each chunk is delivered as a server-sent event (SSE) with a JSON payload."
    ),
)
async def run_agent_stream(request: AgentStreamRequest):
    try:
        runner = AgentExecutor.from_agent_class(
            agent_class=BaseAgent,
            params={"citys": request.citys},
            session_id=request.session_id,
            user_id=request.user_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to create agent runner: {exc}") from exc

    def stream_generator():
        try:
            for chunk in runner.run_stream(ask=request.ask, clear_tool_metadata=request.clear_tool_metadata):
                parsed = runner.parse(chunk)
                payload = json.dumps(parsed, ensure_ascii=False)
                yield f"data: {payload}\n\n"
        except Exception as exc:
            error_payload = json.dumps({"event": "error", "message": str(exc)}, ensure_ascii=False)
            yield f"data: {error_payload}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")


