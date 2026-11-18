"""Recurso 2: subagents=  (delegação de tarefas).

O agente principal ganha a ferramenta `task`, que dispara um subagente com
prompt, ferramentas (e opcionalmente modelo) próprios, em contexto isolado.
Rode:  python 02_subagents.py
Observe: nas "chamadas ao modelo", o principal pede a ferramenta `task`.
"""
from langchain_core.tools import tool

from deepagents import create_deep_agent

from _comum import criar_gateway, mostrar


@tool
def converter_celsius_para_fahrenheit(celsius: float) -> float:
    """Converte graus Celsius para Fahrenheit."""
    return celsius * 9 / 5 + 32


conversor = {
    "name": "conversor",
    "description": "Converte unidades de temperatura. Use sempre que precisar converter temperaturas.",
    "system_prompt": "Você converte temperaturas usando a ferramenta. Responda só com o resultado e a unidade.",
    "tools": [converter_celsius_para_fahrenheit],
    # "model": "openai:gpt-5.4",   # opcional: modelo diferente do principal
}


def main() -> None:
    gw = criar_gateway()
    agent = create_deep_agent(model=gw.build(),
        system_prompt="Você é um coordenador. Delegue conversões de temperatura ao subagente 'conversor'.",
        subagents=[conversor],
    )
    result, rep = gw.run_agent(
        agent,
        {"messages": [{"role": "user", "content": "Quantos graus Fahrenheit são 36.5 Celsius?"}]},
        label="subagents",
    )
    mostrar(result, rep)


if __name__ == "__main__":
    main()
