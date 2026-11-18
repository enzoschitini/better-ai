"""Recurso 5: HarnessProfile  (ajuste de prompt/harness que acompanha o MODELO).

Registrado uma vez, vale sempre que aquele modelo for selecionado, sem mexer
em cada create_deep_agent. Campos: base_system_prompt, system_prompt_suffix,
tool_description_overrides, excluded_tools, excluded_middleware,
extra_middleware, general_purpose_subagent.
Rode:  python 05_harness_profile.py
Observe: o sufixo aparece no FIM do system prompt exibido.
"""
import os

from deepagents import HarnessProfile, register_harness_profile

from _comum import MODELO_PADRAO, criar_gateway, mostrar


def main() -> None:
    spec = os.environ.get("MODELO", MODELO_PADRAO)   # chave "provedor:modelo"

    register_harness_profile(
        spec,
        HarnessProfile(
            system_prompt_suffix="REGRA DO PERFIL: responda em no máximo 3 frases e use português do Brasil."
        ),
    )

    gw = criar_gateway()
    # Sem system_prompt: o que o modelo recebe vem do perfil (+ prompts dos middlewares).
    agent = gw.agent()
    result, rep = gw.run_agent(
        agent,
        {"messages": [{"role": "user", "content": "Explique o que é uma API REST."}]},
        label="harness_profile",
    )
    mostrar(result, rep)


if __name__ == "__main__":
    main()
