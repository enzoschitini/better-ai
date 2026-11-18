"""Recurso 4: skills=  (conhecimento sob demanda).

Só o nome e a descrição da skill ficam no prompt. O agente lê o SKILL.md
completo (via read_file) apenas quando decide que a skill é útil.
Rode:  python 04_skills.py
Observe: em "ferramentas executadas" deve aparecer read_file no SKILL.md.
"""
from deepagents.backends.utils import create_file_data
from langgraph.checkpoint.memory import MemorySaver

from deepagents import create_deep_agent

from _comum import criar_gateway, mostrar

SKILL_MD = """\
---
name: resumo-tecnico
description: Use quando o usuário pedir um resumo técnico de um conceito de programação.
---

# Resumo técnico

Ao resumir um conceito, siga EXATAMENTE este formato:

1. **Em uma frase:** definição curta.
2. **Exemplo em Python:** no máximo 5 linhas de código.
3. **Quando usar:** uma linha.
4. **Armadilha comum:** uma linha.
"""


def main() -> None:
    gw = criar_gateway()
    agent = create_deep_agent(model=gw.build(), skills=["/skills/"], checkpointer=MemorySaver())
    result, rep = gw.run_agent(
        agent,
        {
            "messages": [{"role": "user", "content": "Faça um resumo técnico de context managers em Python."}],
            "files": {"/skills/resumo-tecnico/SKILL.md": create_file_data(SKILL_MD)},
        },
        config={"configurable": {"thread_id": "skills-1"}},
        label="skills",
    )
    mostrar(result, rep)


if __name__ == "__main__":
    main()
