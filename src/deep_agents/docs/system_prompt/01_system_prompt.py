"""Recurso 1: system_prompt=  (o mais simples).

Dá instruções ao agente principal. Aceita str ou SystemMessage.
Rode:  python 01_system_prompt.py
"""
from deepagents import create_deep_agent  # noqa: F401  (usado via gw.agent)

from _comum import criar_gateway, mostrar

INSTRUCOES = """\
Você é um mentor de Python para back-end.
Responda sempre em português do Brasil, de forma curta e direta.
Sempre termine a resposta com uma linha: "Dica: <uma dica prática>".
"""


def main() -> None:
    gw = criar_gateway()
    agent = gw.agent(system_prompt=INSTRUCOES)
    result, rep = gw.run_agent(
        agent,
        {"messages": [{"role": "user", "content": "O que é um decorator em Python?"}]},
        label="system_prompt",
    )
    mostrar(result, rep)


if __name__ == "__main__":
    main()
