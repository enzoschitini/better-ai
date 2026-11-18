"""ProviderRules: tratamento por provedor/modelo (renomear, descartar, fixar parâmetros)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from src.deep_agents.model.model_config import ModelConfig


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
