import streamlit as st

APPS: dict[str, dict] = {
    "about": {
        "label":       "📖 Sobre",
        "description": "Informações sobre a plataforma.",
        "path":        "src/web_applications/applications/about.py",
    },
    "api": {
        "label":       "🔌 API",
        "description": "Endpoints e documentação REST.",
        "path":        "src/web_applications/applications/api.py",
    },
    "contact": {
        "label":       "📬 Contato",
        "description": "Dúvidas, sugestões ou parcerias.",
        "path":        "src/web_applications/applications/contact.py",
    },
}

HOME = st.Page(
    "src/web_applications/applications/home.py",
    title="Home",
    url_path="home",
    default=True,
)

PAGES: dict[str, st.Page] = {
    "home": HOME,
    **{
        slug: st.Page(meta["path"], title=meta["label"], url_path=slug)
        for slug, meta in APPS.items()
    },
}