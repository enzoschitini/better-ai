import streamlit as st
from src.web_applications.utils.pages import PAGES

# ---------------------------------------------------------------------------
# About page — src/web_applications/applications/about.py
# ---------------------------------------------------------------------------

# Esconde nav automática
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] { display: none; }
    </style>
""", unsafe_allow_html=True)

# Sidebar exclusiva desta app
with st.sidebar:
    st.markdown("## 📖 Sobre")
    st.markdown("---")
    st.markdown("Seções")
    st.markdown("- Visão geral\n- Stack\n- Versão")
    st.divider()
    st.page_link(PAGES["home"], label="← Voltar para Home")

# Conteúdo da app
st.title("Sobre o BetterAI")
st.caption("Versão 1.0.0")
st.divider()

# TODO: substitua pelo conteúdo real
st.info("🚧 Aplicação **Sobre** ainda não conectada.")