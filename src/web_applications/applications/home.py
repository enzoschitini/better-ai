import os
import streamlit as st

from dotenv import load_dotenv
from src.web_applications.utils.pages import PAGES, APPS

load_dotenv()

# ---------------------------------------------------------------------------
# Home page — src/web_applications/applications/home.py
# ---------------------------------------------------------------------------

if os.getenv("LOCAL", "false").lower() == "true":
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

else:
    st.title("BetterAI ✦")
    st.caption("Where intelligence finds purpose.")
    st.divider()

    st.image("images/Frame 27346.png")

    st.markdown("#### 🔒 Restricted Access")
    st.markdown("This page is protected by a password. Please contact the administrator to obtain access.")