from google import genai
from google.genai import types
import mimetypes
import os
from dotenv import load_dotenv

load_dotenv()


def edit_GAIS4_multi(
    base_image_paths: list,
    reference_image_paths: list | None = None
) -> dict:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    # --------------------
    # PROMPT
    # --------------------
    parts = [
        types.Part.from_text(
            text="Gere uma imagem seguindo o estilo dessas"
        )
    ]

    # --------------------
    # IMAGENS BASE
    # --------------------
    for path in base_image_paths:
        with open(path, "rb") as f:
            image_bytes = f.read()

        mime_type, _ = mimetypes.guess_type(path)

        parts.append(
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type
            )
        )

    # --------------------
    # IMAGENS DE REFERÊNCIA
    # --------------------
    if reference_image_paths:
        for path in reference_image_paths:
            with open(path, "rb") as f:
                image_bytes = f.read()

            mime_type, _ = mimetypes.guess_type(path)

            parts.append(
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type
                )
            )

    contents = [
        types.Content(
            role="user",
            parts=parts
        )
    ]

    config = types.GenerateContentConfig(
        temperature=0.75,
        top_p=0.85,
        max_output_tokens=1024,
        response_modalities=["IMAGE", "TEXT"],
        image_config=types.ImageConfig(
            aspect_ratio="9:16"
        )
    )

    # --------------------
    # CHAMADA AO MODELO
    # --------------------
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=contents,
        config=config
    )

    # --------------------
    # PARSE DA RESPOSTA
    # --------------------
    text_response = None
    images = []

    if response.candidates:
        for part in response.candidates[0].content.parts:

            if part.text:
                text_response = part.text

            if part.inline_data:
                images.append({
                    "mime_type": part.inline_data.mime_type,
                    "data": part.inline_data.data  # bytes puros
                })

    # --------------------
    # METADATA DE USO
    # --------------------
    usage_metadata = None

    if response.usage_metadata:
        usage_metadata = {
            "prompt_tokens": response.usage_metadata.prompt_token_count,
            "output_tokens": response.usage_metadata.candidates_token_count,
            "total_tokens": response.usage_metadata.total_token_count
        }

    # --------------------
    # JSON FINAL
    # --------------------
    return {
        "text_response": text_response,
        "images": images,
        "usage_metadata": usage_metadata
    }

"""

# class ImageEdit

1. Build Parts (Prompt + Imagens)
2. Config (temperature, top_p, max_tokens, etc)
3. Model Call
4. Response Parse (texto, imagens, metadata)
5. Calc cost (tokens and USD)
6. Save images
7. MongoDB Payload (texto, paths, metadata, cost)
8. Response

"""




import mimetypes

response = edit_GAIS4_multi(
    base_image_paths=[
        "src/image_generation/imgs/base/gen3.png",
        "src/image_generation/imgs/base/gen4.png"
    ]
)

# Pasta de saída (opcional)
output_dir = "outputs"
os.makedirs(output_dir, exist_ok=True)

for idx, image in enumerate(response["images"]):
    mime_type = image["mime_type"]
    image_bytes = image["data"]

    # Descobre extensão pelo mime_type
    ext = mimetypes.guess_extension(mime_type) or ".png"

    file_path = os.path.join(output_dir, f"output_{idx}{ext}")

    with open(file_path, "wb") as f:
        f.write(image_bytes)

    print(f"🖼️ Imagem salva em: {file_path}")




"""
edit_GAIS4_multi(
    base_image_paths=[
        "src/image_generation/imgs/base/gen1.png",
        "src/image_generation/imgs/base/gen2.png"
    ]
    reference_image_paths=[
        "src/image_generation/imgs/base/gen3.png",
        "src/image_generation/imgs/base/gen4.png"
    ]
)


response = {
    "text_response": "Claro, aqui está a imagem solicitada.",
    "images": [#Lista com as imagens]
    "usage_metadata": {
        "prompt_tokens": 100,
        "output_tokens": 100,
        "total_tokens": 200
    }
}
#"""
