"""LLMGateway: fachada única para criar modelos/agentes e coletar métricas.

As demais peças ficam em módulos próprios (um por classe):
  model_config.py, provider_rules.py, metrics.py, metrics_callback.py
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Callable, Iterator

from langchain.chat_models import init_chat_model
from langchain_core.callbacks import BaseCallbackHandler

from src.deep_agents.model.metrics import CallMetrics, RunReport
from src.deep_agents.model.metrics_callback import MetricsCallbackHandler
from src.deep_agents.model.model_config import ModelConfig
from src.deep_agents.model.provider_rules import DEFAULT_RULES, ProviderRules, build_kwargs


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
