import streamlit as st
import uuid
from pathlib import Path

from src.image_generation.image_generator_service import ImageGeneratorService

from src.web_applications.pages.acquarello.prompts import GetPromptStyle
from src.web_applications.pages.acquarello.config import STYLE_MAPPING

st.set_page_config(page_title="BetterAI · Acquarello", page_icon="🎨", layout="wide")

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


class AcquarelloApp:

    ASPECT_RATIO_OPTIONS = {
        "Quadro (1:1)": "1:1",
        "Horizontal (16:9)": "16:9",
        "Vertical (9:16)": "9:16",
    }

    def __init__(self):
        st.set_page_config(page_title="Acquarello", page_icon="🎨")

        # Estado global
        if "option" not in st.session_state:
            st.session_state.option = "Gerar aquarela a partir de texto"

        if "last_user" not in st.session_state:
            st.session_state.last_user = None

        if "last_assistant" not in st.session_state:
            st.session_state.last_assistant = None

        if "style_label" not in st.session_state:
            st.session_state.style_label = list(STYLE_MAPPING.keys())[0]

        if "aspect_ratio_label" not in st.session_state:
            st.session_state.aspect_ratio_label = list(self.ASPECT_RATIO_OPTIONS.keys())[0]

        selected_style = STYLE_MAPPING[st.session_state.style_label]["style_en"]
        self.style_prompts = GetPromptStyle(selected_style)
    
    def _center_image(self, image_path):
        col_left, col_center, col_right = st.columns([1, 2, 1])
        with col_center:
            st.image(image_path)

    # -------------------------
    # HEADER + MENU
    # -------------------------
    def welcome(self):
        # MENU NA SIDEBAR
        with st.sidebar:
            st.title("Acquarello")
            st.markdown("Dê vida às suas ideias ou transforme suas imagens em pinturas no estilo que você quiser.")
            st.markdown("---")
            
            st.session_state.option = st.selectbox(
                "Modalidade de geração",
                options=[
                    "Gerar aquarela a partir de texto",
                    "Gerar aquarela a partir de uma foto"
                ],
                index=0 if st.session_state.option == "Gerar aquarela a partir de texto" else 1,
                key="main_menu"
            )

            st.session_state.style_label = st.selectbox(
                "Estilo da composição",
                options=list(STYLE_MAPPING.keys()),
                index=list(STYLE_MAPPING.keys()).index(st.session_state.style_label)
                if st.session_state.style_label in STYLE_MAPPING
                else 0,
                key="style_menu"
            )

            aspect_ratio_options = list(self.ASPECT_RATIO_OPTIONS.keys())
            st.session_state.aspect_ratio_label = st.selectbox(
                "Tamanho",
                options=aspect_ratio_options,
                index=aspect_ratio_options.index(st.session_state.aspect_ratio_label)
                if st.session_state.aspect_ratio_label in aspect_ratio_options
                else 0,
                key="aspect_ratio_menu"
            )

            selected_style_config = STYLE_MAPPING[st.session_state.style_label]
            st.caption(selected_style_config["description"])
            self.style_prompts = GetPromptStyle(selected_style_config["style_en"])

        selected_style_config = STYLE_MAPPING.get(
            st.session_state.style_label,
            STYLE_MAPPING[list(STYLE_MAPPING.keys())[0]]
        )

        st.title(st.session_state.style_label, text_alignment="center")

        st.markdown(
            "<p style='text-align: center;'>"
            f"{selected_style_config['description']}"
            "</p>",
            unsafe_allow_html=True
        )

        st.write("")
        st.image("src/web_applications/pages/acquarello/images/cover.png")
        st.write("")

    # -------------------------
    # IMAGE GENERATOR
    # -------------------------
    def generate_image(self, user_prompt, instructions, image_bytes=None):
        #pass
        #"""
        selected_aspect_ratio = self.ASPECT_RATIO_OPTIONS.get(
            st.session_state.get("aspect_ratio_label", "1:1 (Quadro)"),
            "1:1"
        )

        service = ImageGeneratorService(
            content_config={
                "aspect_ratio": selected_aspect_ratio,
            }
        )

        parts = service.build_parts(
            user_prompt=user_prompt,
            instructions=instructions,
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
                    user_prompt="Transform this image to the selected style.",
                    instructions=self.style_prompts.image_to_image(),
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