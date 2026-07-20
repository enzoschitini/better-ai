import streamlit as st
import uuid
from pathlib import Path


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

            db_id = st.selectbox(
                "Selecione a base de dados",
                options=list(DATABASES.keys()),
                format_func=lambda k: DATABASES[k]["name"],
            )

            db = DATABASES[db_id]
            st.caption(db["description"])
            st.markdown(f"[Acesse a base]({db['link']})", unsafe_allow_html=True)

    # -------------------------
    # TEXTO -> IMAGEM
    # -------------------------
    def text_to_image(self):
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