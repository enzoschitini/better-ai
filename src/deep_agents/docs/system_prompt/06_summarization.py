"""Recurso 6: SummarizationMiddleware com summary_prompt customizado.

Quando a conversa passa do limite (trigger), as mensagens antigas viram um
resumo, guiado pelo seu summary_prompt. Aqui o gatilho é baixo (6 mensagens)
só para você ver acontecer. O prompt PRECISA conter o marcador {messages}.
Rode:  python 06_summarization.py
"""
from deepagents.backends import StateBackend
from deepagents.middleware import SummarizationMiddleware
from langgraph.checkpoint.memory import MemorySaver

from deepagents import create_deep_agent

from _comum import criar_gateway, mostrar

SUMMARY_PROMPT = """\
Resuma a conversa abaixo em português, em no máximo 5 tópicos curtos:
decisões tomadas, fatos importantes e pendências. Responda só com o resumo.

<messages>
{messages}
</messages>
"""

PERGUNTAS = [
    "Meu projeto se chama Dev Atlas e usa só Python.",
    "Vou hospedar na Oracle Cloud.",
    "Prefiro PostgreSQL para dados relacionais.",
    "Também uso MongoDB para documentos.",
    "Qual era o nome do meu projeto e onde vou hospedar?",
]


def main() -> None:
    gw = criar_gateway()
    resumo = SummarizationMiddleware(
        model=gw.build(),
        backend=StateBackend(),
        summary_prompt=SUMMARY_PROMPT,
        trigger=("messages", 6),   # dispara com 6+ mensagens (padrão é bem maior)
        keep=("messages", 2),      # mantém as 2 mais recentes
    )
    agent = create_deep_agent(model=gw.build(), middleware=[resumo], checkpointer=MemorySaver())  # substitui o padrão pelo mesmo .name
    config = {"configurable": {"thread_id": "sum-1"}}

    for i, p in enumerate(PERGUNTAS, 1):
        print(f"\n>>> Turno {i}: {p}")
        result, rep = gw.run_agent(agent, {"messages": [{"role": "user", "content": p}]},
                                   config=config, label=f"turno-{i}")
        print("   resposta:", result["messages"][-1].text[:200] if hasattr(result["messages"][-1], "text") else "")
        print(f"   mensagens no estado: {len(result['messages'])} | chamadas ao modelo neste turno: {rep.n_calls}")

    mostrar(result, rep)
    print("\nTotais da sessão:", gw.totals())


if __name__ == "__main__":
    main()
