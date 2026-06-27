import streamlit as st
from src.web_applications.utils.pages import PAGES, APPS

# ---------------------------------------------------------------------------
# Home page — src/web_applications/applications/home.py
# ---------------------------------------------------------------------------

st.markdown("""
    <style>
        [data-testid="stSidebarNav"] { display: none; }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## ✦ BetterAI")
    st.markdown("---")
    st.markdown("Selecione uma aplicação abaixo para acessá-la.")

st.title("BetterAI ✦")
st.caption("Where intelligence finds purpose.")
st.divider()

password = st.text_input("Senha de acesso", type="password", placeholder="Digite a senha para acessar as aplicações...")

#if password == "BetterAI":
cols = st.columns(len(APPS))
for col, (slug, meta) in zip(cols, APPS.items()):
    with col:
        st.markdown(f"### {meta['label']}")
        st.write(meta["description"])
        st.page_link(PAGES[slug], label="Abrir →")