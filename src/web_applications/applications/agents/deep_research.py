from typing import Any, Dict, Optional

import streamlit as st

from src.agents.agent_executor import AgentExecutor
from src.agents.trend_radar.agent import BaseAgent
from src.utils.unique_id_factory import IDGenerator

with st.sidebar:
    st.markdown("## ✦ BetterAI")
    st.markdown("### Agente: Deep Research")
    st.markdown("---")
    st.markdown("Pesquisa aprofundada com coleta de fontes e contexto.")
    st.caption("Use este chat para investigar temas em profundidade.")


def collect_tool_payload(chunk: Any, parsed: Dict[str, Any]) -> Optional[Any]:
    event = parsed.get("event") if isinstance(parsed, dict) else None
    tool_name = parsed.get("tool_name") if isinstance(parsed, dict) else None
    is_tool_event = isinstance(event, str) and event.lower() in {
        "toolcallcompleted",
        "tool_call_completed",
    }

    if not is_tool_event and not tool_name:
        return None

    if isinstance(chunk, dict):
        payload = chunk.get("payload")
        if payload is not None:
            return payload

    return None


def get_agent_response(prompt: str):
    runner: Optional[AgentExecutor] = st.session_state.get("trend_radar_runner")
    if runner is None:
        id_generator = IDGenerator()

        runner = AgentExecutor.from_agent_class(
            agent_class=BaseAgent,
            session_id=id_generator.uuid(),
            user_id=id_generator.timestamp(prefix="streamlit_user", separator="-", as_hex=True, suffix_len=6),
        )
        st.session_state.trend_radar_runner = runner

    # Prevent stale tool metadata from previous turns from being emitted again.
    runner.tool_collector.clear()

    for chunk in runner.run_stream(ask=prompt, clear_tool_metadata=True):
        parsed = runner.parse(chunk)
        content = parsed.get("content", "")

        tool_payload = collect_tool_payload(chunk, parsed)
        if tool_payload is not None:
            st.session_state.last_tool_payload = tool_payload

        if content:
            yield content


def render_sources(payload: Any) -> None:
    if payload is None:
        return

    with st.expander("Fontes", expanded=False):
        sources = payload.get("sources") if isinstance(payload, dict) else None
        if isinstance(sources, list) and sources:
            for source in sources:
                if not isinstance(source, dict):
                    continue
                name = source.get("name") or "Fonte"
                url = source.get("url") or source.get("domain")
                if isinstance(url, str) and url.strip():
                    st.markdown(f"- [{name}]({url})")
            return

        st.json(payload)


st.title("Deep Research Chat")
st.caption("Agente BetterAI para pesquisa aprofundada com fontes e contexto confiavel.")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Ola! Sou o agente de Deep Research da BetterAI.\n"
                "Envie sua pergunta e eu faco uma investigacao aprofundada com fontes.\n\n"
                "Exemplos de perguntas:\n"
                "1. O que analistas e imprensa internacional projetam para a Copa do Mundo 2026?\n"
                "2. Quais tendencias de IA generativa devem ganhar mais tracao em 2026?\n"
                "3. Como esta evoluindo a regulacao de IA no Brasil, na UE e nos EUA?\n"
                "4. Quais riscos economicos globais podem impactar os proximos 12 meses?\n"
                "5. Compare estrategias de transicao energetica adotadas na America Latina."
            ),
        }
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        render_sources(message.get("tool_payload"))

if prompt := st.chat_input("Digite sua mensagem"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    st.session_state.messages.append(
        {"role": "assistant", "content": "", "tool_payload": None}
    )
    assistant_message_index = len(st.session_state.messages) - 1

    with st.chat_message("assistant"):
        placeholder = st.empty()

        try:
            st.session_state.last_tool_payload = None
            chunks = []

            for chunk in get_agent_response(prompt):
                chunks.append(chunk)
                partial_reply = "".join(chunks)
                st.session_state.messages[assistant_message_index]["content"] = partial_reply
                placeholder.write(partial_reply)

            reply = "".join(chunks).strip()
            if not reply:
                reply = "Nao consegui gerar uma resposta agora. Tente novamente em instantes."

            st.session_state.messages[assistant_message_index]["content"] = reply
            placeholder.write(reply)

            tool_payload = st.session_state.last_tool_payload
            st.session_state.messages[assistant_message_index]["tool_payload"] = tool_payload
            render_sources(tool_payload)
        except Exception:
            reply = "Falha ao consultar o agente real agora. Tente novamente em instantes."
            st.session_state.messages[assistant_message_index]["content"] = reply
            placeholder.write(reply)

# Test
# O que estão falando da Copa do Mundo 2026

