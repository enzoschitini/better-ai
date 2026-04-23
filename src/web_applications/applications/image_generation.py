import streamlit as st

from src.utils.unique_id_factory import IDGenerator
from src.web_applications.utils.render_components import Component
from src.image_generation.image_generator_service import ImageGeneratorService

class ImageGeneration:
    def __init__(self):
        self.component = Component()

    def _reset_chat(self):
        if "messages" in st.session_state:
            del st.session_state.messages
    
    def head(self):
        self.component.text("Generate Images With Da-Vinci", size=30, align="center")
        st.write("")

    def generate_image(
        self,
        user_prompt="Generate an image of a futuristic city skyline at sunset, with flying cars and neon lights.",
        instructions="Use vibrant colors and a cyberpunk aesthetic.",
        config=None,
        image_bytes=None
    ):
        id_generator = IDGenerator()
        unique_id = id_generator.timestamp()

        service = ImageGeneratorService(content_config=config)

        parts = service.build_parts(
            user_prompt=user_prompt,
            instructions=instructions,
            images=[image_bytes] if image_bytes else None
        )

        config = service.generate_config()
        responses = service.call_model(parts, config)
        result = service.parse_responses(responses)

        image_name = None

        for idx, image_info in enumerate(result["images"]):
            image_bytes = image_info["data"]
            mime_type = image_info["mime_type"]
            extension = "jpg" if mime_type == "image/jpeg" else "png"

            image_name = f"data/img/{unique_id}_{idx + 1}.{extension}"

            with open(image_name, "wb") as f:
                f.write(image_bytes)
            
            return image_name

    def run(self):
        # Inicializa histórico
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # 👇 PRIMEIRO: captura input e atualiza estado
        if prompt := st.chat_input("Digite sua mensagem..."):

            st.session_state.messages.append({
                "role": "user",
                "content": prompt
            })

            config = {
                "temperature": st.session_state.get("temperature", 0.7),
                "aspect_ratio": st.session_state.get("aspect_ratio", "1:1")
            }

            image = self.generate_image(
                user_prompt=prompt,
                instructions=st.session_state.instructions,
                config=config
            )

            st.session_state.messages.append({
                "role": "assistant",
                "content": "Here is a generated image based on your prompt:",
                "image": image
            })

        if len(st.session_state.messages) == 0:
            self.head()

        with st.expander("Config", expanded=False):
            st.write("Here you could show the config used for generation, or allow the user to customize it before generating the image.")

            st.session_state.instructions = st.text_area("Instructions", value="Use vibrant colors.", height=200)
            st.session_state.temperature = st.number_input("Temperature", min_value=0.0, max_value=1.0, value=0.7)
            st.session_state.aspect_ratio = st.selectbox("Dimensions", ["1:1", "3:4", "4:3", "9:16", "16:9"], index=0) 
            st.button("Reset Chat", on_click=self._reset_chat)

        # 👇 Renderiza histórico
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg["role"] == "assistant" and "image" in msg:
                    st.image(msg["image"], caption="Generated Image")




if __name__ == "__main__":
    page = ImageGeneration()
    #r = page.generate_image()
    #print(f"Generated image saved as: {r}")
    page.run()

# python -m src.web_applications.applications.image_generation
# streamlit run src/web_applications/applications/image_generation.py