import streamlit as st
import time
import random
import json
import html
import re
from typing import Any, Dict, Optional

from src.agents.agent_executor import AgentExecutor
from src.agents.trend_radar.agent import BaseAgent
from src.utils.unique_id_factory import IDGenerator

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Chat",
    page_icon="💬",
    layout="centered",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-bottom: 80px !important; }

  /* Caption below chat input */
  .stChatInputContainer ~ div, 
  [data-testid="stBottom"] > div:last-child {
    text-align: center;
  }
  .chat-caption {
    position: fixed;
    bottom: 6px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 0.72rem;
    color: #9ca3af;
    z-index: 9999;
    pointer-events: none;
    white-space: nowrap;
  }

  /* Messages */
  .msg-row { display: flex; margin: 8px 0; }
  .msg-row.user { justify-content: flex-end; }
  .msg-row.bot  { justify-content: flex-start; }

  .bubble {
    max-width: 72%;
    padding: 12px 16px;
    border-radius: 18px;
    font-size: 0.95rem;
    line-height: 1.5;
    word-break: break-word;
    box-shadow: 0 1px 3px rgba(0,0,0,.12);
  }
  .bubble.user {
    background: #4f46e5;
    color: #fff;
    border-bottom-right-radius: 4px;
  }
  .bubble.bot {
    background: #f3f4f6;
    color: #111;
    border-bottom-left-radius: 4px;
  }

  .sources {
    margin-top: 10px;
    border-top: 1px solid #d1d5db;
    padding-top: 8px;
  }
  .sources summary {
    cursor: pointer;
    font-size: .82rem;
    color: #374151;
    user-select: none;
  }
  .sources pre {
    margin: 8px 0 0;
    padding: 8px;
    border-radius: 8px;
    background: #e5e7eb;
    color: #111827;
    font-size: .78rem;
    line-height: 1.35;
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-word;
  }
  .sources-list {
    margin-top: 8px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .source-item {
    font-size: .82rem;
    color: #1f2937;
    line-height: 1.35;
    word-break: break-word;
  }
  .source-item a {
    color: #1d4ed8;
    text-decoration: none;
    font-weight: 600;
  }
  .source-item a:hover {
    text-decoration: underline;
  }

  .avatar {
    width: 32px; height: 32px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; flex-shrink: 0; margin-top: 2px;
  }
  .avatar.bot  { background: #e0e7ff; margin-right: 8px; }
  .avatar.user { background: #c7d2fe; margin-left: 8px; }

  /* Typing dots */
  .typing-bubble {
    background: #f3f4f6;
    border-radius: 18px;
    border-bottom-left-radius: 4px;
    padding: 14px 18px;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    box-shadow: 0 1px 3px rgba(0,0,0,.12);
  }
  .dot {
    width: 8px; height: 8px;
    background: #9ca3af;
    border-radius: 50%;
    animation: bounce 1.2s infinite;
  }
  .dot:nth-child(2) { animation-delay: .2s; }
  .dot:nth-child(3) { animation-delay: .4s; }

  @keyframes bounce {
    0%,60%,100% { transform: translateY(0); opacity: .6; }
    30%          { transform: translateY(-6px); opacity: 1; }
  }
</style>
""", unsafe_allow_html=True)

# ── Mock responses ────────────────────────────────────────────────────────────
MOCK_RESPONSES = [
    "Olá! Sou uma IA simulada. Esta é uma resposta mockada para testar a mecânica do chat. 😊",
    "Interessante pergunta! Como sou um protótipo com dados mockados, minha resposta é pré-definida — mas a interface está funcionando perfeitamente!",
    "Esta é uma demonstração do fluxo de chat: input nativo, spinner de carregamento e bolhas de mensagem. Tudo funcionando! 🚀",
    "Ótimo teste! Note o spinner que aparece enquanto a resposta é 'processada'. Em produção, aqui viria a integração real com a API.",
    "Simulando raciocínio... ✨ Resultado: interface linda e funcional! O st.chat_input fica fixo no rodapé nativamente.",
    "O objetivo é validar a mecânica: envio de mensagem → loading → resposta. Missão cumprida! 🎯",
    "Você digitou algo e eu respondi. Backend mockado, UX real!",
]

def get_mock_response(_: str) -> str:
    time.sleep(random.uniform(1.2, 2.4))
    return random.choice(MOCK_RESPONSES)

def collect_tool_payload(chunk: Any, parsed: Dict[str, Any]) -> Optional[Any]:
  if isinstance(chunk, dict):
    payload = chunk.get("payload")
    if payload is not None:
      return payload

  raw_chunk = parsed.get("raw") if isinstance(parsed, dict) else None
  if isinstance(raw_chunk, dict):
    payload = raw_chunk.get("payload")
    if payload is not None:
      return payload

  return None

def format_sources_html(payload: Any) -> str:
  if payload is None:
    return ""

  def normalize_url(raw_value: Any) -> str:
    if not isinstance(raw_value, str):
      return ""

    text = raw_value.strip()
    markdown_link = re.match(r"^\[[^\]]*\]\(([^\)]+)\)$", text)
    if markdown_link:
      return markdown_link.group(1).strip()

    return text

  sources = payload.get("sources") if isinstance(payload, dict) else None
  if isinstance(sources, list) and sources:
    lines = []
    for source in sources:
      if not isinstance(source, dict):
        continue

      name = source.get("name") or "Fonte"
      url = normalize_url(source.get("url") or source.get("domain"))
      if not url:
        continue

      safe_name = html.escape(str(name))
      safe_href = html.escape(url, quote=True)
      safe_url_text = html.escape(url)
      lines.append(
        f'<div class="source-item"><a href="{safe_href}" target="_blank" rel="noopener noreferrer">{safe_name}</a> ({safe_url_text})</div>'
      )

    if lines:
      return (
        '<details class="sources">'
        '<summary>Fontes</summary>'
        '<div class="sources-list">'
        + "".join(lines)
        + '</div>'
        '</details>'
      )

  pretty_payload = json.dumps(payload, ensure_ascii=False, indent=2)
  safe_payload = html.escape(pretty_payload)
  return (
    '<details class="sources">'
    '<summary>Fontes</summary>'
    f'<pre>{safe_payload}</pre>'
    '</details>'
  )

def get_agent_response(prompt: str):
  runner: Optional[AgentExecutor] = st.session_state.get("trend_radar_runner")
  if runner is None:
    runner = AgentExecutor.from_agent_class(
      agent_class=BaseAgent,
      params={"citys": ["Salvador", "São Paulo", "Rio de Janeiro"]},
      session_id=IDGenerator().uuid(),
      user_id="streamlit_user",
    )
    st.session_state.trend_radar_runner = runner

  for chunk in runner.run_stream(ask=prompt):
    parsed = runner.parse(chunk)
    event_name = parsed.get("event")
    content = parsed.get("content", "")
    tool_name = parsed.get("tool_name")

    tool_payload = collect_tool_payload(chunk, parsed)
    if tool_payload is not None:
      st.session_state.last_tool_payload = tool_payload

    if event_name and event_name != "RunContent":
      suffix = f" [{tool_name}]" if tool_name else ""
      print(f"\n[{event_name}]{suffix}", flush=True)

    if event_name == "ToolCallCompleted":
      print("[ToolPayload]", flush=True)
      print(json.dumps(tool_payload or {}, ensure_ascii=False, indent=2), flush=True)

    if content:
      yield content

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "bot", "text": "Olá! 👋 Sou sua IA de teste. Pode me mandar uma mensagem!"}
    ]
if "thinking" not in st.session_state:
    st.session_state.thinking = False
if "use_real_agent" not in st.session_state:
  st.session_state.use_real_agent = False

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 20px 0 8px;">
  <span style="font-size:2rem;">💬</span>
  <h2 style="margin:4px 0 2px; color:#111;">AI Chat</h2>
  <p style="color:#6b7280; font-size:.85rem; margin:0;">Protótipo com respostas mockadas</p>
</div>
""", unsafe_allow_html=True)

st.divider()

st.session_state.use_real_agent = st.toggle(
  "Usar respostas reais (Trend Radar)",
  value=st.session_state.use_real_agent,
)

mode_caption = "Modo atual: respostas reais" if st.session_state.use_real_agent else "Modo atual: respostas mockadas"
st.caption(mode_caption)

# ── Render messages ───────────────────────────────────────────────────────────
chat_area = st.empty()

def render_messages(thinking: bool = False):
    rendered_html = ""
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            safe_text = html.escape(msg["text"])
            rendered_html += f"""
            <div class="msg-row user">
              <div class="bubble user">{safe_text}</div>
              <div class="avatar user">🧑</div>
            </div>"""
        else:
            safe_text = html.escape(msg["text"])
            sources_html = format_sources_html(msg.get("tool_payload"))
            rendered_html += f"""
            <div class="msg-row bot">
              <div class="avatar bot">🤖</div>
              <div class="bubble bot">{safe_text}{sources_html}</div>
            </div>"""

    if thinking:
        rendered_html += """
        <div class="msg-row bot">
          <div class="avatar bot">🤖</div>
          <div class="typing-bubble">
            <div class="dot"></div><div class="dot"></div><div class="dot"></div>
          </div>
        </div>"""

    rendered_html += '<div id="chat-end"></div>'
    chat_area.markdown(
        f'<div>{rendered_html}</div>'
        '<script>document.getElementById("chat-end").scrollIntoView({{behavior:"smooth"}});</script>',
        unsafe_allow_html=True,
    )

render_messages()

# ── Native chat input (fixed at bottom automatically) ─────────────────────────
#st.markdown('<div class="chat-caption">BetterAI</div>', unsafe_allow_html=True)

if prompt := st.chat_input("Digite sua mensagem…"):
  # 1. Show user message immediately
  st.session_state.messages.append({"role": "user", "text": prompt})
  render_messages(thinking=True)

  # 2. Get response from selected mode
  if st.session_state.use_real_agent:
    try:
      st.session_state.last_tool_payload = None
      has_streamed_content = False

      for chunk in get_agent_response(prompt):
        if not has_streamed_content:
          st.session_state.messages.append({"role": "bot", "text": "", "tool_payload": None})
          has_streamed_content = True

        st.session_state.messages[-1]["text"] += chunk
        render_messages(thinking=False)

      if has_streamed_content and st.session_state.last_tool_payload is not None:
        st.session_state.messages[-1]["tool_payload"] = st.session_state.last_tool_payload
        render_messages(thinking=False)

      if not has_streamed_content:
        st.session_state.messages.append(
          {"role": "bot", "text": "Nao consegui gerar uma resposta agora. Tente novamente em instantes."}
        )
        render_messages(thinking=False)
    except Exception:
      st.session_state.messages.append(
        {"role": "bot", "text": "Falha ao consultar o agente real agora. Tente novamente ou volte para o modo mockado."}
      )
      render_messages(thinking=False)
  else:
    reply = get_mock_response(prompt)
    # 3. Show bot reply
    st.session_state.messages.append({"role": "bot", "text": reply})
    render_messages(thinking=False)
