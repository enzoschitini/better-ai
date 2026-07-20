import streamlit as st
import uuid
from pathlib import Path
import base64


DATABASES = {
    "oboticario": {
        "name": "Oboticário",
        "description": "Base de dados do Grupo O Boticário.",
        "link": "https://www.grupoboticario.com.br/",
    },
    "natura": {
        "name": "Natura",
        "description": "Base de dados da Natura &Co.",
        "link": "https://www.natura.com.br/",
    },
}

LLM_MODELS = {
    "openai": {
        "name": "OpenAI",
        "description": "Modelo de linguagem da OpenAI.",
        "id": "gpt-4",
    },
    "anthropic": {
        "name": "Claude",
        "description": "Modelo de linguagem da Anthropic.",
        "id": "claude-v1",
    },
}


# -------------------------
# CACHE: lê o arquivo do disco e faz base64 uma vez só,
# em vez de a cada rerun/interação da sidebar.
# -------------------------
@st.cache_data
def load_profile_image(path: str) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode()


class ContentGeneratorApp:
    def __init__(self):
        st.set_page_config(page_title="BetterAI · Content Generator", page_icon="📝", layout="wide")

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

    # -------------------------
    # SIDEBAR (FRAGMENT)
    # Interações aqui reexecutam SÓ este fragment, não a página inteira.
    # NÃO usar `with st.sidebar:` aqui dentro — ele vem de fora, no run().
    # -------------------------
    @st.fragment
    def sidebar(self):
        st.title("Gerador de Conteúdo")
        st.markdown("Crie conteúdo textual de forma automatizada.")
        st.markdown("---")

        with st.expander("Base de Dados"):
            db_id = st.selectbox(
                "Selecione a base de dados",
                options=list(DATABASES.keys()),
                format_func=lambda k: DATABASES[k]["name"],
                key="db_id",
            )
            db = DATABASES[db_id]
            st.caption(db["description"])
            st.markdown(f"[Acesse a base]({db['link']})", unsafe_allow_html=True)

        with st.expander("Objetivo"):
            st.text_area(
                "Objetivo",
                placeholder="Digite as instruções aqui...",
                height=200,
                label_visibility="collapsed",
                key="objetivo",
            )

        with st.expander("Requisitos Extras"):
            st.text_area(
                "Requisitos Extras",
                placeholder="Digite os requisitos extras aqui...",
                height=200,
                label_visibility="collapsed",
                key="requisitos",
            )

        with st.expander("Configurações"):
            st.slider(
                "Criatividade",
                min_value=0,
                max_value=100,
                value=50,
                step=1,
                key="criatividade",
            )
            st.slider(
                "Faixa de tamanho do conteúdo",
                min_value=0,
                max_value=2000,
                value=(200, 800),
                step=50,
                key="faixa_tamanho",
            )
            st.selectbox(
                "Selecione o modelo de linguagem",
                options=list(LLM_MODELS.keys()),
                format_func=lambda k: LLM_MODELS[k]["name"],
                key="llm_model_id",
            )

        self._profile_card()

    def _profile_card(self):
        path = "src/web_applications/pages/acquarello/images/cover.png"
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
                width: 44px; height: 44px;
                border-radius: 50%;
                object-fit: cover;
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
    # Lê a configuração atual da sidebar a partir do session_state.
    # Como todos os widgets têm `key=`, os valores estão sempre disponíveis aqui.
    # -------------------------
    def get_config(self) -> dict:
        db_id = st.session_state.get("db_id")
        llm_model_id = st.session_state.get("llm_model_id")
        return {
            "database": DATABASES.get(db_id),
            "objetivo": st.session_state.get("objetivo", ""),
            "requisitos": st.session_state.get("requisitos", ""),
            "criatividade": st.session_state.get("criatividade", 50),
            "faixa_tamanho": st.session_state.get("faixa_tamanho", (200, 800)),
            "llm_model": LLM_MODELS.get(llm_model_id),
        }

    # -------------------------
    # TEXTO -> IMAGEM
    # -------------------------
    def text_to_image(self):
        if "last_user" not in st.session_state:
            st.session_state.last_user = None
        if "last_assistant" not in st.session_state:
            st.session_state.last_assistant = None

        prompt = st.chat_input("Digite algo...")

        if prompt:
            st.session_state.last_user = prompt
            st.session_state.last_assistant = None

        # Mostra última interação
        if st.session_state.last_user:
            with st.chat_message("user"):
                st.markdown(st.session_state.last_user)

        # Gera imagem
        if st.session_state.last_user and st.session_state.last_assistant is None:
            with st.chat_message("assistant"):
                with st.spinner("Gerando composição aquarela..."):
                    config = self.get_config()  # config atual da sidebar

                    image_name = self.generate_image(
                        user_prompt=st.session_state.last_user,
                        instructions=self.style_prompts.text_to_image(),
                        # config=config,  # descomente quando o generate_image aceitar
                    )

                    resposta = "Aqui está a imagem aquarela que você pediu!"
                    st.session_state.last_assistant = resposta

                st.markdown(resposta)

                if image_name:
                    st.image(image_name)

        # Caso já tenha resposta
        elif st.session_state.last_assistant:
            with st.chat_message("assistant"):
                st.markdown(st.session_state.last_assistant)

    # -------------------------
    # ROUTER
    # -------------------------
    def run(self):
        # O `with st.sidebar` fica AQUI (fora do fragment).
        with st.sidebar:
            self.sidebar()
        self.text_to_image()


app = ContentGeneratorApp()
app.run()

# streamlit run web_app.py