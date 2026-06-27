import random
import time
from typing import Any, Dict, Optional

import streamlit as st

from src.agents.agent_executor import AgentExecutor
from src.agents.trend_radar.agent import BaseAgent
from src.utils.unique_id_factory import IDGenerator

MOCK_RESPONSES = [
    "Ola! Esta e uma resposta mockada para testar o chat.",
    "Fluxo de chat funcionando com componentes nativos do Streamlit.",
    "Mensagem recebida. No modo mockado, as respostas sao simuladas.",
    "Tudo certo por aqui. Se quiser, ative o modo real no toggle acima.",
]

with st.sidebar:
    st.markdown("## ✦ BetterAI")
    st.markdown("---")
    st.markdown("Selecione uma aplicação abaixo para acessá-la.")

def get_mock_response(_: str) -> str:
    time.sleep(random.uniform(0.8, 1.4))
    return random.choice(MOCK_RESPONSES)


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
        runner = AgentExecutor.from_agent_class(
            agent_class=BaseAgent,
            params={"citys": ["Salvador", "Sao Paulo", "Rio de Janeiro"]},
            session_id=IDGenerator().uuid(),
            user_id="streamlit_user",
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


st.title("AI Chat")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Ola! Pode enviar sua mensagem."}
    ]

if "use_real_agent" not in st.session_state:
    st.session_state.use_real_agent = False

st.session_state.use_real_agent = st.toggle(
    "Usar respostas reais (Trend Radar)",
    value=st.session_state.use_real_agent,
)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        render_sources(message.get("tool_payload"))

if prompt := st.chat_input("Digite sua mensagem"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()

        if st.session_state.use_real_agent:
            try:
                st.session_state.last_tool_payload = None
                chunks = []

                for chunk in get_agent_response(prompt):
                    chunks.append(chunk)
                    placeholder.write("".join(chunks))

                reply = "".join(chunks).strip()
                if not reply:
                    reply = "Nao consegui gerar uma resposta agora. Tente novamente em instantes."
                placeholder.write(reply)

                tool_payload = st.session_state.last_tool_payload
                render_sources(tool_payload)
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": reply,
                        "tool_payload": tool_payload,
                    }
                )
            except Exception:
                reply = "Falha ao consultar o agente real agora. Tente novamente ou volte para o modo mockado."
                placeholder.write(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
        else:
            reply = get_mock_response(prompt)
            placeholder.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
