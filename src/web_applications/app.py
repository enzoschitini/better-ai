import streamlit as st
from src.web_applications.applications.home import Home

st.set_page_config(page_title="BetterAI", page_icon="AI")

# Estado inicial
if "page" not in st.session_state:
    st.session_state.page = None

# Configuração das páginas
PAGES = {
    "Applications": ["Home", "Text to Aquarela", "Image to Aquarela"],
    "Documentation": ["API", "Tutoriais"]
}

with st.sidebar:
    # Contexto (selectbox sem label)
    context = st.selectbox(
        "",
        ["Applications", "Documentation"],
        label_visibility="collapsed"
    )

    # Botões das páginas
    for page in PAGES[context]:
        if st.button(page, use_container_width=True):
            st.session_state.page = page

# Página padrão (caso nenhuma tenha sido clicada ainda)
if st.session_state.page is None:
    st.session_state.page = PAGES[context][0]

# --- Render ---
if st.session_state.page == "Home":
    home = Home()
    home.run()

# streamlit run src/web_applications/app.py