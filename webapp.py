import streamlit as st
import importlib
import logging
import traceback

from src.web_applications.utils.render_components import Component
from src.web_applications.config import (
    MENU_ITEMS, PAGES
)

# -----------------------------
# Configuração de logs
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

# -----------------------------
# Configuração da página
# -----------------------------
st.set_page_config(
    page_title="BetterAI - Unified AI Platform",
    page_icon="AI",
    #layout="wide",
    initial_sidebar_state="expanded",
    menu_items=MENU_ITEMS
)

class WebAPP:
    # -----------------------------
    # Helpers
    # -----------------------------
    def _get_class_name(self, module_name: str) -> str:
        if module_name.upper() == "API":
            return "API"
        return "".join(word.capitalize() for word in module_name.split("_"))

    def _is_valid_page(self, module_name: str) -> bool:
        for section in PAGES.values():
            for group in section.values():
                if module_name in group.values():
                    return True
        return False

    def _set_page(self, module_name: str):
        logger.info(f"Navigating to page: {module_name}")
        st.session_state.page_module = module_name
        st.query_params["page"] = module_name
        st.rerun()

    def _handle_error(self, title: str, error: Exception = None, debug: bool = False):
        logger.error(f"{title} | {str(error)}")
        
        st.error(f"⚠️ {title}")

        if debug and error:
            st.code(traceback.format_exc())

        if st.button("Voltar para Home"):
            self._set_page("home")

        st.stop()

    #@st.cache_resource
    def _load_page(self, module_name: str):
        module_path = f"src.web_applications.applications.{module_name}"

        try:
            logger.info(f"Loading module: {module_path}")
            module = importlib.import_module(module_path)
        except ModuleNotFoundError as e:
            self._handle_error(
                "Module not found",
                e,
                debug=True
            )

        class_name = self._get_class_name(module_name)

        try:
            page_class = getattr(module, class_name)
        except AttributeError as e:
            self._handle_error(
                f"Class '{class_name}' not found",
                e,
                debug=True
            )

        return page_class
    
    # -----------------------------
    # Main methods
    # -----------------------------

    def single_app(self, module_name: str):
        page_class = self._load_page(module_name)
        page = page_class()
        page.run()
    
    def run(self, module_name: str = None):
        if module_name:
            self.single_app(module_name)
        else:
            self.base_app()

    def base_app(self):
        # -----------------------------
        # Estilos customizados
        # -----------------------------
        component = Component()

        # -----------------------------
        # Estado inicial + URL sync
        # -----------------------------
        query_params = st.query_params

        if "page_module" not in st.session_state:
            st.session_state.page_module = None

        try:
            if "page" in query_params:
                st.session_state.page_module = query_params["page"]
                logger.info(f"Page loaded from URL: {st.session_state.page_module}")
        except Exception as e:
            self._handle_error("Error reading URL parameters.", e, debug=True)


        # -----------------------------
        # Sidebar
        # -----------------------------
        with st.sidebar:
            #component.image("images/idle.png", width=120)
            #st.write("")
            context = st.selectbox(
                "",
                list(PAGES.keys()),
                label_visibility="collapsed"
            )

            current_page = st.session_state.page_module

            for group_name, pages in PAGES[context].items():
                expanded_state = group_name in ["Introduction", "Main", "Docs", "Health"]  # Grupos expandidos por padrão

                with st.expander(group_name, expanded=expanded_state):
                    for label, module_name in pages.items():

                        try:
                            is_active = module_name == current_page

                            if st.button(
                                f"{label}",
                                use_container_width=True,
                                type="primary" if is_active else "secondary"
                            ):
                                self._set_page(module_name)

                        except Exception as e:
                            self._handle_error("Error rendering button", e, debug=True)


        # -----------------------------
        # Página padrão
        # -----------------------------
        if st.session_state.page_module is None:
            try:
                first_group = next(iter(PAGES[context].values()))
                first_page_module = next(iter(first_group.values()))
                logger.info(f"Setting default page: {first_page_module}")
                self._set_page(first_page_module)
            except Exception as e:
                self._handle_error("Error setting default page.", e, debug=True)


        # -----------------------------
        # Validação de página
        # -----------------------------
        if not self._is_valid_page(st.session_state.page_module):
            logger.warning(f"Invalid page: {st.session_state.page_module}")
            self._handle_error("Page not found")


        # -----------------------------
        # Renderização
        # -----------------------------
        try:
            with st.spinner("Loading page..."):
                page_class = self._load_page(st.session_state.page_module)
                page = page_class()

                logger.info(f"Running page: {st.session_state.page_module}")
                page.run()

        except Exception as e:
            self._handle_error("Unexpected error while rendering the page.", e, debug=True)

web_app = WebAPP()
web_app.run("image_generation")

# streamlit run webapp.py