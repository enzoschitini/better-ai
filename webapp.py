import streamlit as st
import importlib

st.set_page_config(page_title="BetterAI", page_icon="AI")

# -----------------------------
# Configuração das páginas
# -----------------------------
PAGES = {
    "Applications": {
        "Main": {
            "Home": "home",
        },
        "Aquarela": {
            "Text to Aquarela": "text_to_aquarela",
            "Image to Aquarela": "image_to_aquarela",
        },
    },
    "Documentation": {
        "Docs": {
            "API": "api",
            "Tutoriais": "tutoriais",
        }
    }
}

# -----------------------------
# Helpers
# -----------------------------
def get_class_name(module_name: str) -> str:
    """
    Converte:
    text_to_aquarela → TextToAquarela
    api → API
    """
    if module_name.upper() == "API":
        return "API"
    return "".join(word.capitalize() for word in module_name.split("_"))


def load_page(module_name: str):
    """
    Import dinâmico seguro
    """
    module_path = f"src.web_applications.applications.{module_name}"
    
    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError:
        st.error(f"Módulo não encontrado: {module_path}")
        st.stop()

    class_name = get_class_name(module_name)

    try:
        page_class = getattr(module, class_name)
    except AttributeError:
        st.error(f"Classe '{class_name}' não encontrada em {module_name}.py")
        st.stop()

    return page_class()


# -----------------------------
# Estado inicial
# -----------------------------
if "page_module" not in st.session_state:
    st.session_state.page_module = None


# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    context = st.selectbox(
        "",
        list(PAGES.keys()),
        label_visibility="collapsed"
    )

    for group_name, pages in PAGES[context].items():
        with st.expander(group_name, expanded=True):
            for label, module_name in pages.items():
                if st.button(label, use_container_width=True):
                    st.session_state.page_module = module_name


# -----------------------------
# Página padrão
# -----------------------------
if st.session_state.page_module is None:
    # pega a primeira página do primeiro grupo
    first_group = next(iter(PAGES[context].values()))
    first_page_module = next(iter(first_group.values()))
    st.session_state.page_module = first_page_module


# -----------------------------
# Renderização
# -----------------------------
page = load_page(st.session_state.page_module)
page.run()


from src.web_applications.config import PAGES

# streamlit run webapp.py