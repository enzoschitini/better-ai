import streamlit as st
from web_app import PAGES

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
st.info("🚧 Aplicação **API** ainda não conectada.")