"""
llm_gateway.py
==============
Interface única para acessar modelos de vários provedores (via LangChain /
Deep Agents) com métricas detalhadas de cada chamada.

Peças:
  - ModelConfig          -> configuração (provedor, id, temperatura, extras)
  - ProviderRules        -> tratamento por provedor/modelo (parâmetros que
                            precisam ser renomeados, descartados ou fixados)
  - CallMetrics          -> métricas de UMA chamada ao LLM
  - RunReport            -> métricas agregadas de uma execução (pode ter
                            várias chamadas, como num agente com ferramentas)
  - MetricsCallbackHandler -> callback do LangChain que alimenta o RunReport
  - LLMGateway           -> fachada: build(), invoke(), stream(), agent()
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Iterator
from uuid import UUID

from langchain.chat_models import init_chat_model
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import LLMResult

# --------------------------------------------------------------------------- #
# Configuração e tratamento por provedor
# --------------------------------------------------------------------------- #


@dataclass
class ModelConfig:
    provider: str                       # "openai", "anthropic", "google_genai", ...
    model_id: str                       # "gpt-5.4", "claude-sonnet-4-6", ...
    temperature: float | None = None
    max_tokens: int | None = None
    timeout: float | None = None        # segundos
    max_retries: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)   # específicos do provedor

    @property
    def spec(self) -> str:
        return f"{self.provider}:{self.model_id}"


@dataclass
class ProviderRules:
    """Ajustes que o gateway aplica antes de criar o modelo.

    rename: nome genérico -> nome que a integração do provedor espera
    drop_if: lista de (predicado_sobre_model_id, [parâmetros a descartar])
    defaults: kwargs aplicados se o usuário não definiu nada
    """
    rename: dict[str, str] = field(default_factory=dict)
    drop_if: list[tuple[Callable[[str], bool], list[str]]] = field(default_factory=list)
    defaults: dict[str, Any] = field(default_factory=dict)


# Pontos de partida. Os nomes de parâmetro divergem entre integrações e mudam
# com as versões: confira a página "chat model integrations" de cada provedor
# e ajuste esta tabela (ou passe a sua em LLMGateway(rules=...)).
DEFAULT_RULES: dict[str, ProviderRules] = {
    # max_tokens genérico -> max_output_tokens no Gemini
    "google_genai": ProviderRules(rename={"max_tokens": "max_output_tokens"}),
    # Modelos de raciocínio da OpenAI costumam rejeitar temperature:
    # descartamos quando o id parece ser de raciocínio (ajuste o predicado).
    "openai": ProviderRules(
        drop_if=[(lambda m: m.startswith(("o1", "o3", "o4")), ["temperature"])],
    ),
    "anthropic": ProviderRules(),
}


def build_kwargs(cfg: ModelConfig, rules: dict[str, ProviderRules]) -> dict[str, Any]:
    r = rules.get(cfg.provider, ProviderRules())
    kwargs: dict[str, Any] = dict(r.defaults)
    generic = {
        "temperature": cfg.temperature,
        "max_tokens": cfg.max_tokens,
        "timeout": cfg.timeout,
        "max_retries": cfg.max_retries,
    }
    kwargs.update({k: v for k, v in generic.items() if v is not None})
    kwargs.update(cfg.extra)
    for predicate, names in r.drop_if:
        if predicate(cfg.model_id):
            for n in names:
                kwargs.pop(n, None)
    return {r.rename.get(k, k): v for k, v in kwargs.items()}


# --------------------------------------------------------------------------- #
# Métricas
# --------------------------------------------------------------------------- #


@dataclass
class CallMetrics:
    run_id: str
    provider: str | None = None
    model_requested: str | None = None
    model_returned: str | None = None        # o que o provedor diz ter usado
    started_at: float = 0.0                  # epoch
    ended_at: float | None = None
    latency_s: float | None = None
    time_to_first_token_s: float | None = None
    streamed: bool = False
    # Tokens
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    reasoning_tokens: int = 0
    audio_in_tokens: int = 0
    audio_out_tokens: int = 0
    usage_source: str = "none"               # "usage_metadata" | "llm_output" | "none"
    # Conteúdo / resultado
    finish_reason: str | None = None
    n_input_messages: int = 0
    input_chars: int = 0
    output_chars: int = 0
    tool_calls: list[str] = field(default_factory=list)   # nomes das ferramentas pedidas
    invalid_tool_calls: int = 0
    response_id: str | None = None
    system_fingerprint: str | None = None
    service_tier: str | None = None
    tags: list[str] = field(default_factory=list)
    invocation_params: dict[str, Any] = field(default_factory=dict)
    # Erro
    error: str | None = None
    error_type: str | None = None
    # Custo (preencha prices em LLMGateway para calcular)
    cost_usd: float | None = None
    # Interno
    _t0: float = field(default=0.0, repr=False)

    @property
    def tokens_per_second(self) -> float | None:
        if self.latency_s and self.output_tokens:
            return self.output_tokens / self.latency_s
        return None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("_t0", None)
        d["tokens_per_second"] = self.tokens_per_second
        return d


@dataclass
class RunReport:
    """Agrega todas as chamadas feitas durante uma execução."""
    run_label: str
    calls: list[CallMetrics] = field(default_factory=list)
    tool_runs: list[dict[str, Any]] = field(default_factory=list)  # ferramentas executadas
    wall_time_s: float | None = None

    def _sum(self, attr: str) -> int:
        return sum(getattr(c, attr) for c in self.calls)

    @property
    def input_tokens(self) -> int: return self._sum("input_tokens")
    @property
    def output_tokens(self) -> int: return self._sum("output_tokens")
    @property
    def total_tokens(self) -> int: return self._sum("total_tokens")
    @property
    def cache_read_tokens(self) -> int: return self._sum("cache_read_tokens")
    @property
    def reasoning_tokens(self) -> int: return self._sum("reasoning_tokens")
    @property
    def n_calls(self) -> int: return len(self.calls)
    @property
    def n_errors(self) -> int: return sum(1 for c in self.calls if c.error)

    @property
    def cost_usd(self) -> float | None:
        costs = [c.cost_usd for c in self.calls if c.cost_usd is not None]
        return sum(costs) if costs else None

    @property
    def llm_time_s(self) -> float:
        return sum(c.latency_s or 0 for c in self.calls)

    def summary(self) -> dict[str, Any]:
        return {
            "run_label": self.run_label,
            "llm_calls": self.n_calls,
            "errors": self.n_errors,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "llm_time_s": round(self.llm_time_s, 3),
            "wall_time_s": None if self.wall_time_s is None else round(self.wall_time_s, 3),
            "tools_executed": len(self.tool_runs),
            "cost_usd": self.cost_usd,
            "models": sorted({c.model_returned or c.model_requested or "?" for c in self.calls}),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary(),
            "calls": [c.to_dict() for c in self.calls],
            "tool_runs": self.tool_runs,
        }


# --------------------------------------------------------------------------- #
# Callback do LangChain
# --------------------------------------------------------------------------- #


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


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


# --------------------------------------------------------------------------- #
# Fachada
# --------------------------------------------------------------------------- #


class LLMGateway:
    def __init__(
        self,
        config: ModelConfig,
        *,
        rules: dict[str, ProviderRules] | None = None,
        prices: dict[str, tuple[float, float]] | None = None,
        on_call_end: Callable[[CallMetrics], None] | None = None,
        extra_callbacks: list[BaseCallbackHandler] | None = None,
        model: Any = None,   # injeção (testes): modelo já pronto
    ) -> None:
        self.config = config
        self.rules = rules or DEFAULT_RULES
        self.prices = prices
        self.on_call_end = on_call_end
        self.extra_callbacks = extra_callbacks or []
        self._model = model
        self.history: list[RunReport] = []

    # -- modelo --
    def build(self):
        if self._model is None:
            kwargs = build_kwargs(self.config, self.rules)
            self._model = init_chat_model(self.config.spec, **kwargs)
        return self._model

    # -- config de execução com o callback --
    def _new_run(self, label: str | None) -> tuple[RunReport, dict[str, Any]]:
        report = RunReport(run_label=label or uuid.uuid4().hex[:8])
        handler = MetricsCallbackHandler(
            report, provider=self.config.provider, prices=self.prices, on_call_end=self.on_call_end,
        )
        return report, {"callbacks": [handler, *self.extra_callbacks]}

    def invoke(self, messages: Any, *, label: str | None = None, **kwargs) -> tuple[Any, RunReport]:
        report, cfg = self._new_run(label)
        t0 = time.perf_counter()
        try:
            result = self.build().invoke(messages, config=cfg, **kwargs)
        finally:
            report.wall_time_s = time.perf_counter() - t0
            self.history.append(report)
        return result, report

    def stream(self, messages: Any, *, label: str | None = None, **kwargs) -> Iterator[Any]:
        """Gera os chunks; ao terminar, o relatório fica em self.history[-1]."""
        report, cfg = self._new_run(label)
        t0 = time.perf_counter()
        try:
            yield from self.build().stream(messages, config=cfg, **kwargs)
        finally:
            report.wall_time_s = time.perf_counter() - t0
            self.history.append(report)

    # -- Deep Agents --
    def agent(self, **create_kwargs):
        """Cria o deep agent usando o modelo já configurado."""
        from deepagents import create_deep_agent
        return create_deep_agent(model=self.build(), **create_kwargs)

    def run_agent(self, agent: Any, payload: dict, *, label: str | None = None,
                  config: dict | None = None, **kwargs) -> tuple[Any, RunReport]:
        report, cfg = self._new_run(label)
        merged = {**(config or {}), "callbacks": [*(config or {}).get("callbacks", []), *cfg["callbacks"]]}
        t0 = time.perf_counter()
        try:
            result = agent.invoke(payload, config=merged, **kwargs)
        finally:
            report.wall_time_s = time.perf_counter() - t0
            self.history.append(report)
        return result, report

    # -- agregado de toda a sessão --
    def totals(self) -> dict[str, Any]:
        return {
            "runs": len(self.history),
            "llm_calls": sum(r.n_calls for r in self.history),
            "input_tokens": sum(r.input_tokens for r in self.history),
            "output_tokens": sum(r.output_tokens for r in self.history),
            "total_tokens": sum(r.total_tokens for r in self.history),
            "cost_usd": (sum(r.cost_usd or 0 for r in self.history)
                         if any(r.cost_usd is not None for r in self.history) else None),
        }
