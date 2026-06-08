import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Any, List, Optional
from pydantic import BaseModel

from src.agents.trend_radar.agent import BaseAgent
from src.agents.agent_executor import AgentExecutor

router = APIRouter(
    prefix="/agents",
    tags=["agents"],
)


class AgentStreamRequest(BaseModel):
    ask: str
    citys: List[str]
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    clear_tool_metadata: bool = False


def _default_serializer(obj: Any) -> Any:
    """Fallback serializer for objects that json.dumps does not natively support
    (e.g. RunContentEvent and other Pydantic/Agno models)."""
    # Pydantic v2
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump()
        except Exception:
            pass
    # Pydantic v1
    if hasattr(obj, "dict") and callable(getattr(obj, "dict")):
        try:
            return obj.dict()
        except Exception:
            pass
    # Enums
    if hasattr(obj, "value") and hasattr(obj, "name"):
        return obj.value
    # Dataclasses / generic objects
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    # Last resort
    return str(obj)


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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create agent runner: {exc}",
        ) from exc

    def stream_generator():
        try:
            for chunk in runner.run_stream(
                ask=request.ask,
                clear_tool_metadata=request.clear_tool_metadata,
            ):
                parsed = runner.parse(chunk)
                payload = json.dumps(
                    parsed,
                    ensure_ascii=False,
                    default=_default_serializer,
                )
                yield f"data: {payload}\n\n"
            # Sinaliza fim do stream (padrão SSE)
            yield "data: [DONE]\n\n"
        except Exception as exc:
            error_payload = json.dumps(
                {"event": "error", "message": str(exc)},
                ensure_ascii=False,
            )
            yield f"data: {error_payload}\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # evita buffering em proxies tipo Nginx
        },
    )

"""
curl --location 'http://localhost:8000/agents/stream' \
--header 'Content-Type: application/json' \
--header 'Accept: text/event-stream' \
--data '{
    "ask": "Quais são as principais tendências de mobilidade urbana?",
    "citys": ["São Paulo", "Rio de Janeiro"],
    "session_id": "session-123",
    "user_id": "user-456",
    "clear_tool_metadata": false
  }'
"""
