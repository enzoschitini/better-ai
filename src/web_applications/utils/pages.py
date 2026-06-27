import streamlit as st

APPS: dict[str, dict] = {
    "trend_radar": {
        "label":       "📈 Trend Radar",
        "description": "Análise e monitoramento de tendências.",
        "path":        "src/web_applications/applications/agents/trend_radar.py",
    },
    "classdoc": {
        "label":       "🧾 ClassDoc",
        "description": "Gerador de docstring e documentação de classe.",
        "path":        "src/web_applications/applications/doc_class.py",
    },
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