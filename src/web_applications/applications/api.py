import streamlit as st
from src.web_applications.utils.pages import PAGES

st.set_page_config(page_title="API · BetterAI", page_icon="🔌", layout="wide")

st.markdown("""
    <style>
        [data-testid="stSidebarNav"] { display: none; }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🔌 API")
    st.markdown("---")
    st.markdown("Endpoints")
    st.markdown("- `/health`\n- `/docs`\n- `/v1/...`")
    st.divider()
    st.page_link(PAGES["home"], label="← Voltar para Home")

st.title("API REST")
st.caption("Base URL: `https://better-ai-deploy-test.onrender.com`")
st.divider()

# TODO: substitua pelo conteúdo real
#st.info("🚧 Aplicação **API** ainda não conectada.")
import streamlit as st
import time
import random

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

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "bot", "text": "Olá! 👋 Sou sua IA de teste. Pode me mandar uma mensagem!"}
    ]
if "thinking" not in st.session_state:
    st.session_state.thinking = False

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 20px 0 8px;">
  <span style="font-size:2rem;">💬</span>
  <h2 style="margin:4px 0 2px; color:#111;">AI Chat</h2>
  <p style="color:#6b7280; font-size:.85rem; margin:0;">Protótipo com respostas mockadas</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── Render messages ───────────────────────────────────────────────────────────
chat_area = st.empty()

def render_messages(thinking: bool = False):
    html = ""
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            html += f"""
            <div class="msg-row user">
              <div class="bubble user">{msg['text']}</div>
              <div class="avatar user">🧑</div>
            </div>"""
        else:
            html += f"""
            <div class="msg-row bot">
              <div class="avatar bot">🤖</div>
              <div class="bubble bot">{msg['text']}</div>
            </div>"""

    if thinking:
        html += """
        <div class="msg-row bot">
          <div class="avatar bot">🤖</div>
          <div class="typing-bubble">
            <div class="dot"></div><div class="dot"></div><div class="dot"></div>
          </div>
        </div>"""

    html += '<div id="chat-end"></div>'
    chat_area.markdown(
        f'<div>{html}</div>'
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

    # 2. Get mock response (with fake delay)
    reply = get_mock_response(prompt)

    # 3. Show bot reply
    st.session_state.messages.append({"role": "bot", "text": reply})
    render_messages(thinking=False)
