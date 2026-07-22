import streamlit as st
import streamlit.components.v1 as components
import uuid
import time
from pathlib import Path
import base64

from src.web_applications.pages.content_generator.config import DATABASES, LLM_MODELS
from src.utils.unique_id_factory import IDGenerator
from src.web_applications.pages.content_generator.markdown_tools import MarkdownTools


@st.cache_resource
def build_backend(db_id: str, llm_model_id: str):
    """Constrói e cacheia tudo que é pesado.
    Trocar db_id ou modelo cria/reaproveita uma instância; não recria a cada slider.
    """
    class _StubStylePrompts:
        def text_to_image(self):
            return "estilo aquarela"

    return {
        "backend": None,
        "style_prompts": _StubStylePrompts(),
    }


@st.cache_data
def load_profile_image(path: str) -> str:
    """Lê o arquivo do disco + base64 uma única vez (cacheado)."""
    return base64.b64encode(Path(path).read_bytes()).decode()


@st.dialog("Sobre o projeto")
def _show_popup():
    st.markdown("OK")
    #if st.button("Fechar", use_container_width=True):
        #st.rerun()


class ContentGeneratorApp:
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

        if "fake_contents" not in st.session_state:
            st.session_state["fake_contents"] = []
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
            st.write(f"Usuário: {self.user_id}")

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
                )

            with st.expander("Configurações"):
                st.slider(
                    "Quantidade de conteúdo",
                    min_value=1, max_value=5, value=2, step=1,
                    key="content_count",
                )
                st.slider(
                    "Faixa de tamanho do conteúdo",
                    min_value=100, max_value=2000, value=(700, 1200), step=50,
                    key="content_size_range",
                )
                st.selectbox(
                    "Modelo de Linguagem (LLM)",
                    options=list(LLM_MODELS.keys()),
                    format_func=lambda k: LLM_MODELS[k]["name"],
                    key="llm_model_id",
                )

            submitted = st.form_submit_button("Aplicar", use_container_width=True)
            if submitted:
                st.session_state["objetivo"] = objetivo_input
                st.session_state["requisitos"] = requisitos_input

        # Descrição da base (fora do form -> reflete o último valor aplicado)
        db_id = st.session_state.get("db_id", next(iter(DATABASES)))
        db = DATABASES[db_id]

        if st.button("ℹ️ Sobre o projeto", use_container_width=True):
            _show_popup()

        self._profile_card()

    def _profile_card(self):
        path = "src/web_applications/utils/images/profile.jpg"
        img_b64 = load_profile_image(path)  # cacheado
        linkedin_url = "https://www.linkedin.com/in/seu-perfil/"

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
            <a href="{linkedin_url}" target="_blank" class="profile-card">
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
        llm_model_id = st.session_state.get("llm_model_id")
        return {
            "db_id": db_id,
            "llm_model_id": llm_model_id,
            "database": DATABASES.get(db_id),
            "llm_model": LLM_MODELS.get(llm_model_id),
            "Objetivo do Conteúdo": st.session_state.get("Objetivo do Conteúdo", ""),
            "requisitos": st.session_state.get("requisitos", ""),
            "criatividade": st.session_state.get("criatividade", 50),
            "faixa_tamanho": st.session_state.get("faixa_tamanho", (200, 800)),
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


    # -------------------------
    # TEXTO
    # -------------------------
    def chat(self):
        import json
        import time
        prompt = st.chat_input("Digite algo para gerar o conteúdo...")

        if prompt:
            with st.spinner("Gerando conteúdo..."):
                with open("src/web_applications/applications/post.json", "r") as f:
                    fake_content = json.load(f)   

                time.sleep(1)  # Simula tempo de processamento

                #st.write(fake_content)
                st.session_state["fake_contents"].append({
                    "prompt": prompt,
                    "content": fake_content,
                })
                st.session_state["scroll_to_last_content"] = True

        total_contents = len(st.session_state["fake_contents"])
        for index, item in enumerate(st.session_state["fake_contents"]):
            if isinstance(item, dict) and "content" in item:
                item_prompt = item.get("prompt", "(sem prompt)")
                content = item["content"]
            else:
                # Backward compatibility for old session data already saved as raw content.
                item_prompt = "(prompt não disponível)"
                content = item

            if index == total_contents - 1:
                st.markdown("<div id='last-content-expander'></div>", unsafe_allow_html=True)

            with st.expander(f"{len(content) if isinstance(content, list) else 1} Posts · **{item_prompt}** ", expanded=index == total_contents - 1):
                posts = content if isinstance(content, list) else [content]

                for post_index, post in enumerate(posts):
                    st.markdown(
                        f"""
                        <div style="display:inline-block;padding:4px 10px;border:1px solid #d0d7de;border-radius:10px;background:#f6f8fa;font-weight:600;margin-bottom:8px;">
                            Post {post_index + 1}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    markdown_text = self.markdown_tools.generate_markdown(post)
                    if not markdown_text:
                        continue

                    st.markdown(markdown_text)
                    self.markdown_tools.copy_markdown_button(markdown_text, button_key=f"copy_markdown_{index}_{post_index}")

                    if post_index < len(posts) - 1:
                        st.markdown("---")

        if st.session_state["scroll_to_last_content"] and total_contents > 0:
            components.html(
                """
                <script>
                const el = window.parent.document.getElementById('last-content-expander');
                if (el) {
                    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                </script>
                """,
                height=0,
            )
            st.session_state["scroll_to_last_content"] = False



    # -------------------------
    # ROUTER
    # -------------------------
    def run(self):
        with st.sidebar:
            self.sidebar()
        self.header()
        self.chat()


app = ContentGeneratorApp()
app.run()

# streamlit run web_app.py