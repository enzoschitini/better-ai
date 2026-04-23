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
        self.component.image("images/idle.png", width=150)
        st.write("")

        self.component.text("Ask your agent to do something!", size=30, align="center")

    def generate_image(
        self,
        user_prompt="Generate an image of a futuristic city skyline at sunset, with flying cars and neon lights.",
        instructions="Use vibrant colors and a cyberpunk aesthetic.",
        image_bytes=None
    ):
        id_generator = IDGenerator()
        unique_id = id_generator.timestamp()

        service = ImageGeneratorService()

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

            import time
            time.sleep(3)  # Simula tempo de processamento
            image = "data/img/1776967078833188700CceF_1.png"

            st.session_state.messages.append({
                "role": "assistant",
                "content": "Here is a generated image based on your prompt:",
                "image": image
            })

        # 👇 DEPOIS: decide o que mostrar no topo
        if len(st.session_state.messages) == 0:
            self.head()
        else:
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