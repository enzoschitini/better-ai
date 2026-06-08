import json
import time
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Any, Dict, Optional
from pydantic import BaseModel

from src.agents.trend_radar.agent import BaseAgent
from src.agents.agent_executor import AgentExecutor

router = APIRouter(
    prefix="/agents",
    tags=["agents"],
)


class AgentStreamRequest(BaseModel):
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    ask: str
    metadata: Optional[Dict[str, Any]] = None
    metadada: Optional[Dict[str, Any]] = None


def _default_serializer(obj: Any) -> Any:
    """Fallback serializer for objects that json.dumps does not natively support
    (e.g. RunContentEvent and other Pydantic/Agno models)."""
    try:
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

    except Exception as e:
        raise TypeError(
            f"Object of type {type(obj).__name__} is not JSON serializable: {str(e)}"
        )


@router.post(
    "/stream",
    summary="Execute the trend radar agent with streamed responses",
    description=(
        "Run the trend radar agent using a simple JSON body and receive events as a streaming response. "
        "Each chunk is delivered as a server-sent event (SSE) with a JSON payload."
    ),
)
async def run_agent_stream(request: AgentStreamRequest):
    request_metadata = request.metadata or request.metadada
    if not request_metadata:
        raise HTTPException(
            status_code=400,
            detail="Field 'metadata' (or 'metadada') is required and must be a JSON object.",
        )

    if "cities" not in request_metadata:
        raise HTTPException(
            status_code=400,
            detail="metadata must contain 'cities'.",
        )

    try:
        runner = AgentExecutor.from_agent_class(
            agent_class=BaseAgent,
            params={"metadata": request_metadata},
            session_id=request.session_id,
            user_id=request.user_id,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create agent runner: {exc}",
        ) from exc

    def stream_generator():
        # Métricas para o MetadataResponse final
        request_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)
        start_perf = time.perf_counter()
        chunk_count = 0
        status = "success"
        error_message: Optional[str] = None

        try:
            init = {
                "event": "StreamStart",
                "message": "Stream started"
            }
            
            yield f"data: {json.dumps(init, ensure_ascii=False, default=_default_serializer)}\n\n"

            for chunk in runner.run_stream(
                ask=request.ask
            ):
                parsed = runner.parse(chunk)
                payload = json.dumps(
                    parsed,
                    ensure_ascii=False,
                    default=_default_serializer,
                )
                chunk_count += 1
                yield f"data: {payload}\n\n"

        except Exception as exc:
            status = "error"
            error_message = str(exc)
            error_payload = json.dumps(
                {"event": "error", "message": error_message},
                ensure_ascii=False,
            )
            yield f"data: {error_payload}\n\n"

        finally:
            finished_at = datetime.now(timezone.utc)
            duration_ms = int((time.perf_counter() - start_perf) * 1000)

            response_metadata = {
                "event": "MetadataResponse",
                "data": {
                    "request_id": request_id,
                    "session_id": request.session_id,
                    "user_id": request.user_id,
                    "status": status,
                    "error": error_message,
                    "chunk_count": chunk_count,
                    "started_at": started_at.isoformat(),
                    "finished_at": finished_at.isoformat(),
                    "duration_ms": duration_ms,
                    "input": {
                        "ask": request.ask,
                        "metadata": request_metadata,
                    },
                },
            }
            yield f"data: {json.dumps(response_metadata, ensure_ascii=False, default=_default_serializer)}\n\n"

            # Sinaliza fim do stream (padrão SSE)
            #yield "data: [DONE]\n\n"
            end = {
                "event": "StreamEnd",
                "message": "Stream finished"
            }

            yield f"data: {json.dumps(end, ensure_ascii=False, default=_default_serializer)}\n\n"

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
        "metadata": {
            "cities": ["São Paulo", "Rio de Janeiro"]
        },
    "session_id": "session-123",
    "user_id": "user-456"
  }'
"""
