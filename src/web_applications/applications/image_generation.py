import streamlit as st
from src.image_generation.image_generator_service import ImageGeneratorService

class ImageGeneration:
    def __init__(self):
        pass

    def generate_image(self, image_bytes=None):
        service = ImageGeneratorService()

        parts = service.build_parts(
            user_prompt="Generate an image of a futuristic city skyline at sunset, with flying cars and neon lights.",
            instructions="Use vibrant colors and a cyberpunk aesthetic.",
            images=[image_bytes] if image_bytes else None
        )

        config = service.generate_config()
        responses = service.call_model(parts, config)
        result = service.parse_responses(responses)

        image_name = None

    def app(self):
        st.title("BetterAI — Base Page")
        st.write("### Where Intelligence Finds Purpose")

    def run(self):
        self.app()

if __name__ == "__main__":
    page = ImageGeneration()
    page.run()

# streamlit run src/web_applications/applications/image_generation.py