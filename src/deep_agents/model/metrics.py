"""CallMetrics (uma chamada ao LLM) e RunReport (agregado de uma execução)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


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
