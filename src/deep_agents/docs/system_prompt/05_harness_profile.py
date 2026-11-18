"""Recurso 5: HarnessProfile  (ajuste de prompt/harness que acompanha o MODELO).

Registrado uma vez, vale sempre que aquele modelo for selecionado, sem mexer
em cada create_deep_agent. Este exemplo usa os 7 campos do perfil:

  base_system_prompt          -> slot BASE do prompt (vem depois do seu system_prompt=)
  system_prompt_suffix        -> slot SUFFIX, no FIM do prompt
  tool_description_overrides  -> reescreve a descrição de ferramentas
  excluded_tools              -> esconde ferramentas do modelo
  excluded_middleware         -> remove middlewares da pilha
  extra_middleware            -> acrescenta middlewares à pilha
  general_purpose_subagent    -> ajusta/desliga o subagente padrão (e, com isso, a `task`)

Rode:  python 05_harness_profile.py
Observe:
  - o prompt exibido tem BASE (meio) e SUFFIX (fim);
  - o modelo não recebe as ferramentas `execute` nem `task` (o prompt não as menciona) e vê a descrição nova do `ls`;
  - o middleware extra imprime uma linha "[extra_middleware]" a cada chamada ao modelo.
"""
import os

from deepagents import GeneralPurposeSubagentProfile, HarnessProfile, register_harness_profile
from langchain.agents.middleware import AgentMiddleware

from _comum import MODELO_PADRAO, criar_gateway, mostrar


class ContaChamadas(AgentMiddleware):
    """extra_middleware: exemplo mínimo. Roda antes de cada chamada ao modelo."""

    def __init__(self) -> None:
        super().__init__()
        self.n = 0

    def before_model(self, state, runtime):
        self.n += 1
        print(f"[extra_middleware] chamada ao modelo nº {self.n} ({len(state['messages'])} mensagens)")
        return None


def criar_perfil() -> HarnessProfile:
    return HarnessProfile(
        # BASE: texto fixo do "harness", logo depois do system_prompt= do agente (que aqui não existe).
        base_system_prompt="Você é um assistente técnico. Seja direto e preciso.",
        # SUFFIX: último bloco do prompt, o mais perto do histórico da conversa.
        system_prompt_suffix="REGRA DO PERFIL: responda em no máximo 3 frases e use português do Brasil.",
        # Troca a descrição que o modelo lê da ferramenta `ls` (chave com nome errado = no-op silencioso).
        tool_description_overrides={"ls": "Lista os arquivos do diretório virtual. (descrição do perfil)"},
        # Some da lista de ferramentas do modelo (calibragem, não segurança).
        excluded_tools=frozenset({"execute"}),
        # Remove o middleware de resumo da pilha. Nome que não casa com nada na pilha é rejeitado.
        excluded_middleware=frozenset({"SummarizationMiddleware"}),
        # Função sem argumentos: cada pilha recebe sua própria instância.
        extra_middleware=lambda: [ContaChamadas()],
        # enabled=False remove o subagente general-purpose; sem outros subagentes, a `task` some também.
        general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False),
    )


def main() -> None:
    spec = os.environ.get("MODELO", MODELO_PADRAO)   # chave "provedor:modelo"

    register_harness_profile(spec, criar_perfil())

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
