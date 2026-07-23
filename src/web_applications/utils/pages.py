import streamlit as st

APPS: dict[str, dict] = {
    "deep_research": {
        "label":       "📈 Deep Research",
        "description": "Pesquisa profunda com análise e monitoramento de tendências.",
        "path":        "src/web_applications/applications/agents/deep_research.py",
    },
    "knowledgebase_agent": {
        "label":       "📚 Agente Base de Conhecimento",
        "description": "Agente para consulta e gerenciamento de base de conhecimento.",
        "path":        "src/web_applications/applications/agents/knowlegbase_agent.py",
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
    "acquarello": {
        "label":       "🎨 Acquarello",
        "description": "Gere imagens em aquarela a partir de texto ou imagens.",
        "path":        "src/web_applications/applications/acquarello.py",
    },
    "content_generator": {
        "label":       "📝 Gerador de Conteúdo",
        "description": "Crie conteúdo textual de forma automatizada.",
        "path":        "src/web_applications/applications/content_generator.py",
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