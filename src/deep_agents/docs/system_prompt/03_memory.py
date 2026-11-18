"""Recurso 3: memory=  (arquivos AGENTS.md carregados na inicialização).

Contexto fixo (convenções, preferências, regras do projeto) que entra no prompt
sempre. O arquivo precisa existir no backend ANTES de criar o agente: aqui
semeamos o StateBackend padrão passando `files` no input.
Rode:  python 03_memory.py
"""
from deepagents.backends.utils import create_file_data
from langgraph.checkpoint.memory import MemorySaver

from deepagents import create_deep_agent

from _comum import criar_gateway, mostrar

AGENTS_MD = """\
# Convenções do projeto
- Linguagem: apenas Python (back-end). Nunca sugira JavaScript ou TypeScript.
- Estilo: type hints em todas as funções públicas.
- Nome do projeto: Dev Atlas.
"""


def main() -> None:
    gw = criar_gateway()
    agent = create_deep_agent(model=gw.build(),
        memory=["/AGENTS.md"],
        checkpointer=MemorySaver(),   # como na doc
    )
    result, rep = gw.run_agent(
        agent,
        {
            "messages": [{"role": "user", "content": "Quais convenções do projeto você deve seguir? Cite o nome do projeto."}],
            "files": {"/AGENTS.md": create_file_data(AGENTS_MD)},   # semeia o backend (caminho virtual começa com "/")
        },
        config={"configurable": {"thread_id": "memory-1"}},
        label="memory",
    )
    mostrar(result, rep)


if __name__ == "__main__":
    main()
