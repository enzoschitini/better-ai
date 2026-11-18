"""Utilidades compartilhadas pelos exemplos (nada específico de Deep Agents aqui).

Variáveis de ambiente:
  MODELO         provedor:modelo   (padrão: anthropic:claude-sonnet-4-6)
  MOSTRAR_PROMPT 1/0               mostra o system prompt que o modelo recebeu (padrão: 1)
  PROMPT_MAX     nº de caracteres do prompt exibido (padrão: 3000)
"""
from __future__ import annotations

import json
import os
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler

from llm_gateway import LLMGateway, ModelConfig, RunReport

MODELO_PADRAO = "anthropic:claude-sonnet-4-6"


class PromptSpy(BaseCallbackHandler):
    """Imprime o system prompt exato da PRIMEIRA chamada ao modelo."""

    raise_error = False

    def __init__(self, max_chars: int = 3000) -> None:
        self.max_chars = max_chars
        self.done = False

    def on_chat_model_start(self, serialized, messages, **kwargs):
        if self.done:
            return
        self.done = True
        for m in messages[0]:
            if getattr(m, "type", "") == "system":
                texto = m.text if isinstance(getattr(m, "text", None), str) else str(m.content)
                corte = texto[: self.max_chars]
                extra = "" if len(texto) <= self.max_chars else f"\n... [+{len(texto) - self.max_chars} caracteres]"
                print("\n=== SYSTEM PROMPT ENVIADO AO MODELO (1ª chamada) ===")
                print(corte + extra)
                print("=" * 52)
                return
        print("\n=== (a 1ª chamada não tinha system prompt) ===")


def criar_gateway() -> LLMGateway:
    spec = os.environ.get("MODELO", MODELO_PADRAO)
    provider, _, model_id = spec.partition(":")
    spies = []
    if os.environ.get("MOSTRAR_PROMPT", "1") != "0":
        spies.append(PromptSpy(int(os.environ.get("PROMPT_MAX", "3000"))))
    return LLMGateway(ModelConfig(provider, model_id, temperature=0), extra_callbacks=spies)


def texto_final(result: dict[str, Any]) -> str:
    msg = result["messages"][-1]
    t = getattr(msg, "text", None)
    return t if isinstance(t, str) else str(msg.content)


def mostrar(result: dict[str, Any], rep: RunReport) -> None:
    print("\n=== RESPOSTA FINAL ===")
    print(texto_final(result))
    print("\n=== CHAMADAS AO MODELO ===")
    for i, c in enumerate(rep.calls, 1):
        pedidas = ", ".join(c.tool_calls) or "-"
        print(f"{i:>2}. in={c.input_tokens} out={c.output_tokens} "
              f"{(c.latency_s or 0):.2f}s  parou: {c.finish_reason}  ferramentas pedidas: {pedidas}")
    if rep.tool_runs:
        print("\n=== FERRAMENTAS EXECUTADAS ===")
        for t in rep.tool_runs:
            print(f"- {t['name']} ({t['duration_s']}s){' ERRO ' + t['error'] if t['error'] else ''}")
    print("\n=== RESUMO ===")
    print(json.dumps(rep.summary(), indent=2, ensure_ascii=False))
