import streamlit as st

from src.utils.unique_id_factory import IDGenerator
from src.image_generation.image_generator_service import ImageGeneratorService

class ImageGeneration:
    def __init__(self):
        pass

    def generate_image(self, image_bytes=None):
        id_generator = IDGenerator()
        unique_id = id_generator.timestamp()

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

        for idx, image_info in enumerate(result["images"]):
            image_bytes = image_info["data"]
            mime_type = image_info["mime_type"]
            extension = "jpg" if mime_type == "image/jpeg" else "png"

            image_name = f"data/img/{unique_id}_{idx + 1}.{extension}"

            with open(image_name, "wb") as f:
                f.write(image_bytes)
            
            return image_name

    def app(self):
        st.title("BetterAI — Base Page")
        st.write("### Where Intelligence Finds Purpose")

        if st.button("Generate Image"):
            image = self.generate_image()
            st.image(image, caption="Generated Image")

    def run(self):
        self.app()

if __name__ == "__main__":
    page = ImageGeneration()
    #r = page.generate_image()
    #print(f"Generated image saved as: {r}")
    page.run()

# python -m src.web_applications.applications.image_generation
# streamlit run src/web_applications/applications/image_generation.py