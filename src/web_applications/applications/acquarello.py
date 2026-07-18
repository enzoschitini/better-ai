import streamlit as st
import uuid
from pathlib import Path

import streamlit as st
from src.web_applications.utils.pages import PAGES
from src.image_generation.image_generator_service import ImageGeneratorService

from src.web_applications.pages.acquarello.prompts import (
    WATERCOLOR_INSTRUCTIONS,
    IMAGE_TO_IMAGE_INSTRUCTIONS
)

st.set_page_config(page_title="API · BetterAI", page_icon="🔌", layout="wide")

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

with st.sidebar:
    st.markdown("## 🔌 API")
    st.markdown("---")
    st.markdown("Endpoints")
    st.markdown("- `/health`\n- `/docs`\n- `/v1/...`")
    st.divider()
    st.page_link(PAGES["home"], label="← Voltar para Home")


class AcquarelloApp:

    def __init__(self):
        st.set_page_config(page_title="Acquarello", page_icon="🎨")

        # Estado global
        if "option" not in st.session_state:
            st.session_state.option = "Gerar imagem a partir de texto"

        if "last_user" not in st.session_state:
            st.session_state.last_user = None

        if "last_assistant" not in st.session_state:
            st.session_state.last_assistant = None
    
    def _center_image(self, image_path):
        col_left, col_center, col_right = st.columns([1, 2, 1])
        with col_center:
            st.image(image_path)

    # -------------------------
    # HEADER + MENU
    # -------------------------
    def welcome(self):
        st.title("Acquarello", text_alignment="center")

        st.markdown(
            "<p style='text-align: center;'>"
            "Dê vida às suas ideias ou transforme suas imagens em pinturas em aquarela"
            "</p>",
            unsafe_allow_html=True
        )

        st.write("")
        #self._center_image("src/web_applications/pages/acquarello/cover.png")
        st.image("src/web_applications/pages/acquarello/cover.png")
        st.write("")

        # MENU (AGORA CORRETO E ÚNICO)
        st.session_state.option = st.selectbox(
            "Escolha uma opção",
            options=[
                "Gerar aquarela a partir de texto",
                "Gerar aquarela a partir de uma foto"
            ],
            index=0 if st.session_state.option == "Gerar imagem a partir de texto" else 1,
            key="main_menu"
        )

    # -------------------------
    # IMAGE GENERATOR
    # -------------------------
    def generate_image(self, user_prompt, image_bytes=None):
        #pass
        #"""
        service = ImageGeneratorService()

        parts = service.build_parts(
            user_prompt=user_prompt,
            instructions=WATERCOLOR_INSTRUCTIONS,
            images=[image_bytes] if image_bytes else None
        )

        config = service.generate_config()
        responses = service.call_model(parts=parts, config=config)
        result = service.parse_responses(responses=responses)

        image_name = None
        output_dir = Path("_cache_generated_images")
        output_dir.mkdir(parents=True, exist_ok=True)

        for idx, image_info in enumerate(result["images"]):
            image_bytes = image_info["data"]
            mime_type = image_info["mime_type"]
            extension = "jpg" if mime_type == "image/jpeg" else "png"

            image_name = output_dir / f"{uuid.uuid4()}_{idx + 1}.{extension}"

            with open(image_name, "wb") as f:
                f.write(image_bytes)

        return str(image_name) if image_name else None
        #"""

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
                        user_prompt=st.session_state.last_user
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
    # FOTO -> IMAGEM
    # -------------------------
    def image_to_image(self):
        uploaded_file = st.file_uploader(
            "Faça upload de uma imagem",
            type=["jpg", "jpeg", "png"],
            max_upload_size=10,
            accept_multiple_files=False
        )

        if uploaded_file:
            with st.spinner("Gerando composição aquarela..."):
                image_name = self.generate_image(
                    user_prompt=IMAGE_TO_IMAGE_INSTRUCTIONS,
                    image_bytes=uploaded_file.read()
                )

            if image_name:
                st.image(image_name)

    # -------------------------
    # ROUTER
    # -------------------------
    def run(self):
        self.welcome()

        if st.session_state.option == "Gerar aquarela a partir de texto":
            self.text_to_image()

        elif st.session_state.option == "Gerar aquarela a partir de uma foto":
            self.image_to_image()

app = AcquarelloApp()
app.run()

# Run app comand
# streamlit run app.py