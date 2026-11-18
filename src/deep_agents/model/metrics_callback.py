"""MetricsCallbackHandler: callback do LangChain que alimenta o RunReport."""

from __future__ import annotations

import threading
import time
from typing import Any, Callable
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import LLMResult

from src.deep_agents.model.metrics import CallMetrics, RunReport


def _extract_usage(msg: AIMessage | None, llm_output: dict | None, m: CallMetrics) -> None:
    """Preenche tokens. Prefere usage_metadata (padronizado pelo LangChain)."""
    um = getattr(msg, "usage_metadata", None) if msg is not None else None
    if um:
        m.usage_source = "usage_metadata"
        m.input_tokens = int(um.get("input_tokens", 0) or 0)
        m.output_tokens = int(um.get("output_tokens", 0) or 0)
        m.total_tokens = int(um.get("total_tokens", 0) or (m.input_tokens + m.output_tokens))
        itd = um.get("input_token_details") or {}
        otd = um.get("output_token_details") or {}
        m.cache_read_tokens = int(itd.get("cache_read", 0) or 0)
        m.cache_creation_tokens = int(itd.get("cache_creation", 0) or 0)
        m.audio_in_tokens = int(itd.get("audio", 0) or 0)
        m.reasoning_tokens = int(otd.get("reasoning", 0) or 0)
        m.audio_out_tokens = int(otd.get("audio", 0) or 0)
        return
    tu = (llm_output or {}).get("token_usage") or (llm_output or {}).get("usage")
    if tu:  # formato legado, varia por provedor
        m.usage_source = "llm_output"
        m.input_tokens = int(tu.get("prompt_tokens") or tu.get("input_tokens") or 0)
        m.output_tokens = int(tu.get("completion_tokens") or tu.get("output_tokens") or 0)
        m.total_tokens = int(tu.get("total_tokens") or (m.input_tokens + m.output_tokens))


class MetricsCallbackHandler(BaseCallbackHandler):
    """Coleta uma CallMetrics por chamada ao LLM e um registro por ferramenta.

    Seguro para threads (o LangChain pode chamar callbacks de threads diferentes).
    """

    raise_error = False  # nunca derruba a execução por causa de métrica

    def __init__(
        self,
        report: RunReport,
        provider: str | None = None,
        prices: dict[str, tuple[float, float]] | None = None,
        on_call_end: Callable[[CallMetrics], None] | None = None,
    ) -> None:
        self.report = report
        self.provider = provider
        self.prices = prices or {}
        self.on_call_end = on_call_end
        self._lock = threading.Lock()
        self._open: dict[UUID, CallMetrics] = {}
        self._tools: dict[UUID, dict[str, Any]] = {}

    # ---- início ---------------------------------------------------------- #
    def _start(self, run_id: UUID, serialized: dict | None, messages: list[list[BaseMessage]] | None,
               prompts: list[str] | None, tags: list[str] | None, kwargs: dict) -> None:
        inv = dict(kwargs.get("invocation_params") or {})
        for secret in ("api_key", "openai_api_key", "anthropic_api_key", "google_api_key"):
            inv.pop(secret, None)
        m = CallMetrics(run_id=str(run_id), provider=self.provider)
        m.model_requested = inv.get("model") or inv.get("model_name") or inv.get("_type")
        m.invocation_params = inv
        m.tags = list(tags or [])
        m.started_at = time.time()
        m._t0 = time.perf_counter()
        if messages:
            flat = [x for batch in messages for x in batch]
            m.n_input_messages = len(flat)
            m.input_chars = sum(len(str(x.content)) for x in flat)
        elif prompts:
            m.n_input_messages = len(prompts)
            m.input_chars = sum(len(p) for p in prompts)
        with self._lock:
            self._open[run_id] = m

    def on_chat_model_start(self, serialized, messages, *, run_id, tags=None, **kwargs):
        self._start(run_id, serialized, messages, None, tags, kwargs)

    def on_llm_start(self, serialized, prompts, *, run_id, tags=None, **kwargs):
        self._start(run_id, serialized, None, prompts, tags, kwargs)

    # ---- streaming ------------------------------------------------------- #
    def on_llm_new_token(self, token, *, run_id, **kwargs):
        with self._lock:
            m = self._open.get(run_id)
            if m is not None:
                m.streamed = True
                if m.time_to_first_token_s is None:
                    m.time_to_first_token_s = time.perf_counter() - m._t0

    # ---- fim ------------------------------------------------------------- #
    def on_llm_end(self, response: LLMResult, *, run_id, **kwargs):
        with self._lock:
            m = self._open.pop(run_id, None)
        if m is None:
            return
        m.ended_at = time.time()
        m.latency_s = time.perf_counter() - m._t0

        gen = response.generations[0][0] if response.generations and response.generations[0] else None
        msg = getattr(gen, "message", None)
        _extract_usage(msg if isinstance(msg, AIMessage) else None, response.llm_output, m)

        if isinstance(msg, AIMessage):
            rm = msg.response_metadata or {}
            m.model_returned = rm.get("model_name") or rm.get("model") or rm.get("model_id")
            m.finish_reason = rm.get("finish_reason") or rm.get("stop_reason")
            m.system_fingerprint = rm.get("system_fingerprint")
            m.service_tier = rm.get("service_tier")
            m.response_id = msg.id or rm.get("id")
            m.tool_calls = [tc.get("name", "?") for tc in (msg.tool_calls or [])]
            m.invalid_tool_calls = len(msg.invalid_tool_calls or [])
            m.output_chars = len(msg.text if hasattr(msg, "text") and isinstance(msg.text, str)
                                 else str(msg.content))
        elif gen is not None:
            m.output_chars = len(getattr(gen, "text", "") or "")

        m.cost_usd = self._cost(m)
        self._finish(m)

    def on_llm_error(self, error, *, run_id, **kwargs):
        with self._lock:
            m = self._open.pop(run_id, None)
        if m is None:
            return
        m.ended_at = time.time()
        m.latency_s = time.perf_counter() - m._t0
        m.error = str(error)[:500]
        m.error_type = type(error).__name__
        self._finish(m)

    # ---- ferramentas ----------------------------------------------------- #
    def on_tool_start(self, serialized, input_str, *, run_id, **kwargs):
        with self._lock:
            self._tools[run_id] = {
                "name": (serialized or {}).get("name") or kwargs.get("name"),
                "t0": time.perf_counter(),
            }

    def _tool_done(self, run_id: UUID, error: str | None) -> None:
        with self._lock:
            t = self._tools.pop(run_id, None)
            if t:
                self.report.tool_runs.append({
                    "name": t["name"],
                    "duration_s": round(time.perf_counter() - t["t0"], 4),
                    "error": error,
                })

    def on_tool_end(self, output, *, run_id, **kwargs):
        self._tool_done(run_id, None)

    def on_tool_error(self, error, *, run_id, **kwargs):
        self._tool_done(run_id, f"{type(error).__name__}: {str(error)[:300]}")

    # ---- util ------------------------------------------------------------ #
    def _cost(self, m: CallMetrics) -> float | None:
        """prices: {modelo: (USD por 1M tokens de entrada, USD por 1M de saída)}."""
        for key in (m.model_returned, m.model_requested):
            if key and key in self.prices:
                pin, pout = self.prices[key]
                return (m.input_tokens * pin + m.output_tokens * pout) / 1_000_000
        return None

    def _finish(self, m: CallMetrics) -> None:
        with self._lock:
            self.report.calls.append(m)
        if self.on_call_end:
            try:
                self.on_call_end(m)
            except Exception:  # callback do usuário não pode quebrar a chamada
                pass
