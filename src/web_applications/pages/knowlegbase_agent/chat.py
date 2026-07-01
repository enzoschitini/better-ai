import streamlit as st

from typing import TYPE_CHECKING, Any, Dict, Optional
from html import escape

if TYPE_CHECKING:
    from src.agents.agent_executor import AgentExecutor

def chat(session_id: str, user_id: str, knowledgebase_id: str):
    with st.sidebar:
        st.markdown("## ✦ BetterAI")
        st.markdown("### Agente: Base de Conhecimento")
        st.markdown("---")
        st.markdown("Busca, consulta e gerenciamento de informacoes da base de conhecimento.")
        st.caption("Use este chat para localizar respostas, organizar dados e validar fontes internas.")

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
        runner: Optional["AgentExecutor"] = st.session_state.get("knowledgebase_runner")
        if runner is None:
            # Lazy imports avoid expensive agent stack initialization during first page render.
            from src.agents.agent_executor import AgentExecutor
            from src.agents.knowlegbase_agent.agent import KnowledgeBaseAgent

            print(f"Initializing KnowledgeBaseAgent runner for session_id={session_id}, user_id={user_id}, knowledgebase_id={knowledgebase_id}...")

            runner = AgentExecutor.from_agent_class(
                agent_class=KnowledgeBaseAgent,
                session_id=session_id,
                user_id=user_id,
                params={
                    "filter_search": {"collection_id": knowledgebase_id}
                },
            )
            st.session_state.knowledgebase_runner = runner

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
            files = payload.get("files") if isinstance(payload, dict) else None
            if isinstance(files, list) and files:
                file_names: list[str] = []

                for file_item in files:
                    if not isinstance(file_item, dict):
                        continue

                    name = file_item.get("name")
                    ext = file_item.get("ext")

                    if not isinstance(name, str) or not name.strip():
                        continue

                    normalized_name = name.strip()
                    if isinstance(ext, str) and ext.strip():
                        normalized_ext = ext.strip().lstrip(".")
                        if normalized_ext and not normalized_name.lower().endswith(f".{normalized_ext.lower()}"):
                            normalized_name = f"{normalized_name}.{normalized_ext}"

                    file_names.append(normalized_name)

                if file_names:
                    unique_names = list(dict.fromkeys(file_names))
                    st.caption(f"Arquivos utilizados ({len(unique_names)})")

                    chips = "".join(
                        (
                            "<span style='display:inline-block;padding:6px 10px;margin:4px;"
                            "border:1px solid #d6d8dc;border-radius:999px;background:#f7f8fa;"
                            "font-size:0.85rem;line-height:1.2;'>"
                            f"{escape(file_name)}"
                            "</span>"
                        )
                        for file_name in unique_names
                    )
                    st.markdown(f"<div>{chips}</div>", unsafe_allow_html=True)
                    return

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


    st.title("Base de Conhecimento Chat")
    st.caption("Agente BetterAI para consulta e gerenciamento da base de conhecimento.")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Ola! Sou o agente de Base de Conhecimento da BetterAI.\n"
                    "Envie sua pergunta para consultar, organizar e gerenciar informacoes da base.\n\n"
                    "Exemplos de perguntas:\n"
                    "1. Quais documentos temos sobre politica de acesso e controle de dados?\n"
                    "2. Resuma os principais procedimentos de onboarding registrados na base.\n"
                    "3. Liste fontes e artefatos relacionados ao projeto SCRUM-106.\n"
                    "4. O que mudou na documentacao de API no ultimo ciclo?\n"
                    "5. Encontre referencias para criar um guia de uso da base de conhecimento."
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