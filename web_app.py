import streamlit as st

st.set_page_config(
    page_title="BetterAI",
    page_icon="✦",
    layout="wide",
)

# Esconde a navegação automática do Streamlit entre pages
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] { display: none; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Registry — cada entrada vira um card na home
# "slug" deve bater com o nome do arquivo em pages/
# ---------------------------------------------------------------------------
APPS = {
    "about":   {"label": "📖 Sobre",   "description": "Informações sobre a plataforma."},
    "api":     {"label": "🔌 API",     "description": "Endpoints e documentação REST."},
    "contact": {"label": "📬 Contato", "description": "Dúvidas, sugestões ou parcerias."},
}

# ---------------------------------------------------------------------------
# Sidebar da base — só aparece aqui
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ✦ BetterAI")
    st.markdown("---")
    st.markdown("Selecione uma aplicação abaixo para acessá-la.")

# ---------------------------------------------------------------------------
# Home: lista de cards para cada app
# ---------------------------------------------------------------------------
st.title("BetterAI ✦")
st.caption("Where intelligence finds purpose.")
st.divider()

cols = st.columns(len(APPS))
for col, (slug, meta) in zip(cols, APPS.items()):
    with col:
        st.markdown(f"### {meta['label']}")
        st.write(meta["description"])
        st.page_link(f"pages/{slug}.py", label=f"Abrir →")

# streamlit run web_app.py