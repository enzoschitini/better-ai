"""
Tool Agent Orchestrator — LangChain + Python
============================================
Componentes:
  1. Prompt  — SystemMessage customizável com instruções do agente
  2. Memória — ConversationBufferMemory persistindo o histórico
  3. Tools   — Ferramentas registradas e invocadas automaticamente
"""
import os
from dotenv import load_dotenv

from langchain.agents import AgentExecutor, create_tool_calling_agent  # ← genérico
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.language_models import BaseChatModel               # ← tipo base

from app.agent.build.tool_collector.toolkit import Toolkit  # ← classe que define as ferramentas e coleta dados

load_dotenv()

# ──────────────────────────────────────────────
# 1. PROMPT
# ──────────────────────────────────────────────
SYSTEM_PROMPT = """
Você é Orion, um assistente inteligente e prestativo.

Você possui acesso a ferramentas para buscar informações, consultar dados e acessar uma base de conhecimento.

Diretrizes:
- Responda sempre em português do Brasil.
- Seja claro, objetivo e útil.
- Utilize as ferramentas disponíveis sempre que necessário para garantir respostas corretas e contextualizadas.
- Sempre considere que informações relevantes podem existir na base de conhecimento antes de responder.
- Ao receber perguntas sobre pessoas, termos, projetos, contexto, referências ou informações específicas, priorize consultar a base antes de concluir que não sabe a resposta.
- Não faça suposições quando uma ferramenta puder confirmar a informação.
- Caso a base não contenha informações suficientes, então peça esclarecimentos ao usuário.
- Use o histórico da conversa como contexto adicional para decidir quando consultar ferramentas.
- Antes de responder, reflita se consultar a base pode melhorar a precisão da resposta.

Histórico da conversa está disponível para contexto.
"""


def build_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])


# ──────────────────────────────────────────────
# 2. MEMÓRIA
# ──────────────────────────────────────────────
def build_memory() -> ConversationBufferMemory:
    return ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="output",
    )


# ──────────────────────────────────────────────
# 3. PROVIDERS DISPONÍVEIS
# ──────────────────────────────────────────────
def get_llm(provider: str, model: str, temperature: float) -> BaseChatModel:
    """
    Retorna o LLM correto para o provider escolhido.
    Todos implementam BaseChatModel — o agente não sabe a diferença.
    """
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, temperature=temperature)
    
    """
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model, temperature=temperature)

    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model, temperature=temperature)

    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model=model, temperature=temperature)

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model, temperature=temperature)
    """

    raise ValueError(
        f"Provider '{provider}' não suportado. "
        "Escolha: openai | anthropic | google | groq | ollama"
    )


# ──────────────────────────────────────────────
# 4. ORQUESTRADOR
# ──────────────────────────────────────────────
def build_agent(
    provider: str = "openai",
    model: str = "gpt-4o-mini",
    temperature: float = 0.0,
) -> AgentExecutor:
    """
    Monta e retorna o AgentExecutor completo.

    Args:
        provider:    provedor do LLM (openai | anthropic | google | groq | ollama)
        model:       modelo a usar (ex: 'claude-3-5-haiku-latest', 'gemini-2.0-flash')
        temperature: criatividade do modelo (0 = determinístico)

    Returns:
        AgentExecutor pronto para receber inputs
    """
    llm = get_llm(provider, model, temperature)

    toolkit = Toolkit()
    tools   = toolkit.get_tools()

    prompt = build_prompt()
    memory = build_memory()

    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10,
        return_intermediate_steps=True,
    )

    return executor, toolkit.collector   # ← collector viaja junto


# ──────────────────────────────────────────────
# ENTRY POINT — loop de conversa interativo
# ──────────────────────────────────────────────
def main():
    agent, collector = build_agent(provider="openai", model="gpt-4o-mini")

    print("\n🤖 Agente Orion iniciado. Digite 'sair' para encerrar.\n")

    while True:
        user_input = input("Você: ").strip()
        if not user_input or user_input.lower() in ("sair", "exit", "quit", "cls"):
            break

        collector.clear()                           # limpa dados do turno anterior
        result = agent.invoke({"input": user_input})
        print(f"\nOrion: {result['output']}\n")

        # ── inspeciona dados laterais do turno ──────────────
        side_data = collector.get_all()
        if side_data:
            print("── Dados laterais das tools ──")
            for entry in side_data:
                print(f"  [{entry.tool_name}] {entry.payload} | {entry.timestamp}")
            print()


if __name__ == "__main__":
    main()

# python -m app.agent.build.tool_collector.agent_executor