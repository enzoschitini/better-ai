import streamlit as st

st.set_page_config(
    page_title="BetterAI",
    page_icon="✦",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------
params = st.query_params
page = params.get("page", "home")

# ---------------------------------------------------------------------------
# Registry — adicione aqui cada aplicação real
# Formato: "slug": {"label": "...", "title": "...", "description": "..."}
# ---------------------------------------------------------------------------
APPS = {
    "home": {
        "label": "🏠 Home",
        "title": "BetterAI ✦",
        "description": "Selecione uma aplicação no menu lateral.",
    },
    "about": {
        "label": "📖 Sobre",
        "title": "Sobre",
        "description": "Informações sobre a plataforma BetterAI.",
    },
    "api": {
        "label": "🔌 API",
        "title": "API",
        "description": "Documentação e endpoints da API REST.",
    },
    "contact": {
        "label": "📬 Contato",
        "title": "Contato",
        "description": "Dúvidas, sugestões ou parcerias.",
    },
}

# ---------------------------------------------------------------------------
# Sidebar — gerado automaticamente a partir do registry
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ✦ BetterAI")
    st.markdown("---")
    for slug, meta in APPS.items():
        is_active = page == slug
        weight = "font-weight:700; text-decoration:underline;" if is_active else "text-decoration:none; color:inherit;"
        st.markdown(
            f'<a href="?page={slug}" style="{weight}">{meta["label"]}</a>',
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# Page rendering
# ---------------------------------------------------------------------------
if page not in APPS:
    st.error(f"Página `{page}` não encontrada.")
    st.markdown("[← Voltar para Home](?page=home)")
    st.stop()

meta = APPS[page]
st.title(meta["title"])
st.caption(meta["description"])

st.divider()

# ---------------------------------------------------------------------------
# Aqui entra o conteúdo real de cada página.
# Substitua o bloco st.info(...) pela sua aplicação.
# ---------------------------------------------------------------------------
if page == "home":
    # TODO: cole aqui o código da aplicação Home
    st.info("🚧 Aplicação **Home** ainda não conectada.")

elif page == "about":
    # TODO: cole aqui o código da aplicação Sobre
    st.info("🚧 Aplicação **Sobre** ainda não conectada.")

elif page == "api":
    # TODO: cole aqui o código da aplicação API
    st.info("🚧 Aplicação **API** ainda não conectada.")

elif page == "contact":
    # TODO: cole aqui o código da aplicação Contato
    st.info("🚧 Aplicação **Contato** ainda não conectada.")

# streamlit run webapp.py