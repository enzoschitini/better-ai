import streamlit as st

st.set_page_config(page_title="Sobre · BetterAI", page_icon="📖", layout="wide")

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
    st.page_link("app.py", label="← Voltar para Home")

# Conteúdo da app
st.title("Sobre o BetterAI")
st.caption("Versão 1.0.0")
st.divider()

# TODO: substitua pelo conteúdo real
st.info("🚧 Aplicação **Sobre** ainda não conectada.")