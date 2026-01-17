# https://github.com/enzoschitini/Asimov-Academy/tree/main/Google%20Ai/Nano%20Banana/doc
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import mimetypes
import os

from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def edit_GAIS4_multi(base_image_paths: list, reference_image_paths=None):
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    # --------------------
    # PROMPT SEMÂNTICO CLARO
    # --------------------
    parts = [
        types.Part.from_text(
            text="""
Gere uma imagem seguindo o estilo dessas
"""
        )
    ]

    # --------------------
    # IMAGEM BASE
    # --------------------
    for path in base_image_paths:
        with open(path, "rb") as f:
            base_bytes = f.read()

        base_mime, _ = mimetypes.guess_type(path)

        parts.append(
            types.Part.from_bytes(
                data=base_bytes,
                mime_type=base_mime
            )
        )

    # --------------------
    # IMAGENS DE REFERÊNCIA
    # --------------------
    if reference_image_paths:
        for path in reference_image_paths:
            with open(path, "rb") as f:
                ref_bytes = f.read()

            ref_mime, _ = mimetypes.guess_type(path)

            parts.append(
                types.Part.from_bytes(
                    data=ref_bytes,
                    mime_type=ref_mime
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
        stop_sequences=[
            """1""",
            """3""",
        ],
        response_modalities=[
            "IMAGE",
            "TEXT",
        ],
        system_instruction=[
            types.Part.from_text(text="""

"""),
        ],
        image_config=types.ImageConfig(
            aspect_ratio="9:16",
        ),
    )

    # --------------------
    # CHAMADA SEM STREAM
    # --------------------
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=contents,
        config=config,
    )

    # --------------------
    # TEXTO + IMAGEM
    # --------------------
    image_index = 0

    if response.candidates:
        for part in response.candidates[0].content.parts:

            # TEXTO
            if part.text:
                print("TEXTO:", part.text)

            # IMAGEM
            if part.inline_data:
                ext = mimetypes.guess_extension(part.inline_data.mime_type)
                file_name = f"output_{image_index}{ext}"
                image_index += 1

                with open(file_name, "wb") as f:
                    f.write(part.inline_data.data)

                print(f"🖼️ Imagem salva: {file_name}")

    # --------------------
    # METADATA DE CONSUMO
    # --------------------
    if response.usage_metadata:
        print("\n📊 USO DE TOKENS:")
        print("Prompt tokens:", response.usage_metadata.prompt_token_count)
        print("Resposta tokens:", response.usage_metadata.candidates_token_count)
        print("Total tokens:", response.usage_metadata.total_token_count)

    return response


edit_GAIS4_multi(
    base_image_paths=[
        "src/image_generation/imgs/base/gen3.png",
        "src/image_generation/imgs/base/gen4.png"
    ]

)

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
#"""
