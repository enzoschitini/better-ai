import streamlit as st
from src.web_applications.utils.pages import PAGES

st.set_page_config(page_title="Contato · BetterAI", page_icon="📬", layout="wide")

st.markdown("""
    <style>
        [data-testid="stSidebarNav"] { display: none; }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 📬 Contato")
    st.markdown("---")
    st.markdown("Links")
    st.markdown("- [LinkedIn](https://www.linkedin.com/in/enzoschitini/)")
    st.markdown("- [GitHub](https://github.com/enzoschitini)")
    st.divider()
    st.page_link(PAGES["home"], label="← Voltar para Home")

st.title("Contato")
st.divider()

# TODO: substitua pelo conteúdo real
st.info("🚧 Aplicação **Contato** ainda não conectada.")