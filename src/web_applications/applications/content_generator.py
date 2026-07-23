import base64

import streamlit as st
from pathlib import Path

from src.utils.unique_id_factory import IDGenerator
from src.web_applications.pages.content_generator.markdown_tools import MarkdownTools
from src.web_applications.pages.content_generator.chat import Chat

from src.web_applications.pages.content_generator.config import (
    DATABASES,
    LLM_MODELS,
    DEFAULT_OBJECTIVE,
    LINKEDIN_URL,
    PROFILE_IMAGE_PATH,
    DEFAULT_LINGUAGES,
)

class ContentGeneratorApp:
    @staticmethod
    @st.cache_resource
    def build_backend(db_id: str, llm_model_id: str):
        """
        Constrói e cacheia tudo que é pesado.
        Trocar db_id ou modelo cria/reaproveita uma instância; não recria a cada slider.
        """

        class _StubStylePrompts:
            def text_to_image(self):
                return "estilo aquarela"

        return {
            "backend": None,
            "style_prompts": _StubStylePrompts(),
        }

    @staticmethod
    @st.cache_data
    def load_profile_image(path: str) -> str:
        """Lê o arquivo do disco + base64 uma única vez (cacheado)."""
        return base64.b64encode(Path(path).read_bytes()).decode()

    @staticmethod
    @st.dialog("Sobre o projeto")
    def _show_popup():
        st.markdown("OK")
        #if st.button("Fechar", use_container_width=True):
            #st.rerun()

    def __init__(self):
        st.set_page_config(
            page_title="BetterAI · Content Generator",
            page_icon="📝",
            layout="wide",
        )

        self.id_generator = IDGenerator()
        self.markdown_tools = MarkdownTools()

        if "content_generator_user_id" not in st.session_state:
            st.session_state["content_generator_user_id"] = self.id_generator.timestamp(prefix='USER', separator='_')
        self.user_id = st.session_state["content_generator_user_id"]

        if "generated_contents" not in st.session_state:
            st.session_state["generated_contents"] = []
        if "scroll_to_last_content" not in st.session_state:
            st.session_state["scroll_to_last_content"] = False

        st.markdown("""
            <style>
                [data-testid="stSidebarNav"] { display: none; }
                .block-container {
                    max-width: 980px;
                    margin-left: auto;
                    margin-right: auto;
                    padding-left: 1rem;
                    padding-right: 1rem;
                }

                [data-testid="stChatInput"] {
                    max-width: 980px;
                    margin-left: auto;
                    margin-right: auto;
                }
            </style>
        """, unsafe_allow_html=True)

    def sidebar(self):
        with st.form("config_form", border=False):
            st.title("Gerador de Conteúdo")
            st.markdown("Crie conteúdo textual de forma automatizada.")
            st.markdown("---")

            with st.expander("Base de Dados", expanded=True):
                st.selectbox(
                    "Selecione a base de dados",
                    options=list(DATABASES.keys()),
                    format_func=lambda k: DATABASES[k]["name"],
                    key="db_id",
                )

            with st.expander("Objetivo do Conteúdo"):
                objetivo_input = st.text_area(
                    "Objetivo do Conteúdo",
                    placeholder=(
                        "Descreva o objetivo do conteúdo que deseja gerar.\n\n"
                        "Ex.: Escrever artigos de blog para atrair leads no topo do funil, "
                        "com tom informativo e linguagem acessível. Público-alvo: pequenos "
                        "empreendedores. Foco em resolver dúvidas comuns sobre gestão financeira."
                    ),
                    height=200,
                    label_visibility="collapsed",
                    key="objective_input",
                )

            with st.expander("Requisitos Extras"):
                requisitos_input = st.text_area(
                    "Requisitos Extras",
                    placeholder=(
                        "Adicione instruções ou restrições específicas (opcional).\n\n"
                        "Ex.: Evitar jargões técnicos. Incluir uma chamada para ação ao final. "
                        "Usar subtítulos. Não mencionar concorrentes. Manter tom formal."
                    ),
                    height=200,
                    label_visibility="collapsed",
                    key="extra_requirements",
                )

            with st.expander("Configurações"):
                st.slider(
                    "Quantidade de conteúdo",
                    min_value=1, max_value=5, value=2, step=1,
                    key="content_count",
                )
                st.slider(
                    "Máximo de resultados (contexto)",
                    min_value=5, max_value=25, value=5, step=1,
                    key="max_results",
                )
                st.slider(
                    "Faixa de tamanho do conteúdo",
                    min_value=100, max_value=2000, value=(700, 1200), step=50,
                    key="content_size_range",
                )
                st.selectbox(
                    "Modelo de Linguagem (LLM)",
                    options=list(LLM_MODELS.keys()),
                    format_func=lambda k: LLM_MODELS[k]["id"],
                    key="llm_model_id",
                )

                st.selectbox(
                    "Idioma",
                    options=list(DEFAULT_LINGUAGES.keys()),
                    format_func=lambda k: DEFAULT_LINGUAGES[k]["name"],
                    key="language_id",
                )

            submitted = st.form_submit_button("Aplicar", use_container_width=True)
            if submitted:
                st.session_state["objetivo"] = objetivo_input
                st.session_state["requisitos"] = requisitos_input

        # Descrição da base (fora do form -> reflete o último valor aplicado)
        db_id = st.session_state.get("db_id", next(iter(DATABASES)))
        db = DATABASES[db_id]

        if st.button("ℹ️ Sobre o projeto", use_container_width=True):
            self._show_popup()

        self._profile_card()

    def _profile_card(self):
        img_b64 = self.load_profile_image(PROFILE_IMAGE_PATH)

        st.markdown(
            """
            <style>
            .profile-card {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 10px 14px;
                margin-top: 20px;
                border: 2px solid rgba(255,255,255,.15);
                border-radius: 16px;
                text-decoration: none !important;
                transition: all .2s ease;
            }
            .profile-card:hover {
                border-color: #0a66c2;
                background: rgba(10,102,194,.10);
            }
            .profile-avatar {
                width: 44px !important;
                height: 44px !important;
                min-width: 44px;
                border-radius: 50%;
                object-fit: cover !important;
                object-position: center;
                display: block;
                flex-shrink: 0;
            }
            .profile-name {
                flex: 1;
                font-weight: 600;
                font-size: 1.05rem;
                color: inherit;
            }
            .profile-arrow {
                font-size: 24px;
                color: #9aa0a6;
                line-height: 1;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <a href="{LINKEDIN_URL}" target="_blank" class="profile-card">
                <img src="data:image/png;base64,{img_b64}" class="profile-avatar" />
                <span class="profile-name">Enzo Schitini</span>
                <span class="profile-arrow">&rsaquo;</span>
            </a>
            """,
            unsafe_allow_html=True,
        )

    # -------------------------
    # Config atual (lida do session_state, sempre disponível)
    # -------------------------
    def get_config(self) -> dict:
        db_id = st.session_state.get("db_id")
        llm_model_key_or_id = st.session_state.get("llm_model_id", next(iter(LLM_MODELS)))
        language_key_or_id = st.session_state.get("language_id", next(iter(DEFAULT_LINGUAGES)))

        if llm_model_key_or_id in LLM_MODELS:
            llm_model = LLM_MODELS[llm_model_key_or_id]
            llm_model_id = llm_model["id"]
        else:
            llm_model = next(
                (model for model in LLM_MODELS.values() if model["id"] == llm_model_key_or_id),
                None,
            )
            llm_model_id = llm_model_key_or_id

        if language_key_or_id in DEFAULT_LINGUAGES:
            language = DEFAULT_LINGUAGES[language_key_or_id]
            language_id = language["id"]
        else:
            language = next(
                (item for item in DEFAULT_LINGUAGES.values() if item["id"] == language_key_or_id),
                None,
            )
            language_id = language_key_or_id
        language_prompt = (language or {}).get("prompt", "")

        return {
            "db_id": db_id,
            "llm_model_id": llm_model_id,
            "language_id": language_id,
            "language_prompt": language_prompt,
            "database": DATABASES.get(db_id),
            "llm_model": llm_model,
            "language": language,
            "objective_input": (st.session_state.get("objective_input") or "").strip() or DEFAULT_OBJECTIVE,
            "extra_requirements": st.session_state.get("extra_requirements", ""),
            "content_count": st.session_state.get("content_count", 2),
            "max_results": st.session_state.get("max_results", 5),
            "content_size_range": st.session_state.get("content_size_range", (200, 800)),
        }
    
    def header(self):
        config = self.get_config()
        database = config["database"]
        database_header = database["header"]

        st.image(database_header["image"], width=200)
        st.title(database_header["title"])
        st.markdown(database_header["description"])
        st.markdown(f"[Acesse a base]({database['link']})", unsafe_allow_html=True)
        
        st.markdown("---")

    def chat(self):
        chat = Chat(get_config=self.get_config, markdown_tools=self.markdown_tools)
        chat.chat()

    def run(self):
        with st.sidebar:
            self.sidebar()
        self.header()
        self.chat()


app = ContentGeneratorApp()
app.run()

# streamlit run web_app.py