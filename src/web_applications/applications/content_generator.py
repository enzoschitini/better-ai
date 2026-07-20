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
    # HEADER + MENU
    # -------------------------
    def sidebar(self):
        with st.sidebar:
            st.title("Gerador de Conteúdo")
            st.markdown("Crie conteúdo textual de forma automatizada.")
            st.markdown("---")

            with st.expander("Base de Dados"):
                db_id = st.selectbox(
                    "Selecione a base de dados",
                    options=list(DATABASES.keys()),
                    format_func=lambda k: DATABASES[k]["name"],
                )

                db = DATABASES[db_id]
                st.caption(db["description"])
                st.markdown(f"[Acesse a base]({db['link']})", unsafe_allow_html=True)

            with st.expander("Objetivo"):
                st.text_area("", placeholder="Digite as instruções aqui...", height=200, label_visibility="collapsed")
            
            with st.expander("Requisitos Extras"):
                st.text_area("", placeholder="Digite os requisitos extras aqui...", height=200, label_visibility="collapsed")
            
            with st.expander("Configurações"):
                st.slider(
                    "Criatividade",
                    min_value=0,
                    max_value=100,
                    value=50,
                    step=1,
                )
                st.slider(
                    "Faixa de tamanho do conteúdo",
                    min_value=0,
                    max_value=2000,
                    value=(200, 800),
                    step=50,
                )

                llm_model_id = st.selectbox(
                    "Selecione o modelo de linguagem",
                    options=list(LLM_MODELS.keys()),
                    format_func=lambda k: LLM_MODELS[k]["name"],
                )

                llm_model = LLM_MODELS[llm_model_id]
            
            self._profile_card()



    def _profile_card(self):
        path = "src/web_applications/pages/acquarello/images/cover.png"
        img_b64 = base64.b64encode(Path(path).read_bytes()).decode()
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
                    image_name = self.generate_image(
                        user_prompt=st.session_state.last_user,
                        instructions=self.style_prompts.text_to_image()
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
        self.sidebar()
        self.text_to_image()

app = ContentGeneratorApp()
app.run()

# streamlit run web_app.py