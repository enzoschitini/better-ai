# https://github.com/enzoschitini/Asimov-Academy/tree/main/Google%20Ai/Nano%20Banana/doc
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import mimetypes
import os

from dotenv import load_dotenv

load_dotenv()

client = genai.Client()

def create():
    # Generate an image from a text prompt
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents="A high-resolution, studio-lit product photograph of a minimalist ceramic coffee mug in matte black, presented on a polished concrete surface. The lighting is a three-point softbox setup designed to create soft, diffused highlights and eliminate harsh shadows. The camera angle is a slightly elevated 45-degree shot to showcase its clean lines. Ultra-realistic, with sharp focus on the steam rising from the coffee. Square image.",
    )

    image_parts = [
        part.inline_data.data
        for part in response.candidates[0].content.parts
        if part.inline_data
    ]

    if image_parts:
        image = Image.open(BytesIO(image_parts[0]))
        image.save('product_mockup.png')
        image.show()

def edit():
    # Base image prompt: "A photorealistic picture of a fluffy ginger cat sitting on a wooden floor, looking directly at the camera. Soft, natural light from a window."
    image_input = Image.open('/path/to/your/cat_photo.png')
    text_input = """Using the provided image of my cat, please add a small, knitted wizard hat on its head. Make it look like it's sitting comfortably and not falling off."""

    # Generate an image from a text prompt
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[text_input, image_input],
    )

    image_parts = [
        part.inline_data.data
        for part in response.candidates[0].content.parts
        if part.inline_data
    ]

    if image_parts:
        image = Image.open(BytesIO(image_parts[0]))
        image.save('cat_with_hat.png')
        image.show()

def compose():
    # Base image prompts:
    # 1. Woman: "A professional headshot of a woman with brown hair and blue eyes, wearing a plain black t-shirt, against a neutral studio background."
    # 2. Logo: "A simple, modern logo with the letters 'G' and 'A' in a white circle."
    woman_image = Image.open('/path/to/your/woman.png')
    logo_image = Image.open('/path/to/your/logo.png')
    text_input = """Take the first image of the woman with brown hair, blue eyes, and a neutral expression. Add the logo from the second image onto her black t-shirt. Ensure the woman's face and features remain completely unchanged. The logo should look like it's naturally printed on the fabric, following the folds of the shirt."""

    # Generate an image from a text prompt
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[woman_image, logo_image, text_input],
    )

    image_parts = [
        part.inline_data.data
        for part in response.candidates[0].content.parts
        if part.inline_data
    ]

    if image_parts:
        image = Image.open(BytesIO(image_parts[0]))
        image.save('woman_with_logo.png')
        image.show()











############################################################
# GOOGLE AI STUDIO
############################################################

# To run this code you need to install the following dependencies:
# pip install google-genai

def generate_GAIS():
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    result = client.models.generate_images(
        model="models/imagen-4.0-generate-001",
        prompt="""An evocative image of an English afternoon tea table in a period drama setting, specifically reminiscent of the Queen Elizabeth I era. The table is adorned with a newspaper, prominently displaying the headline 'Gemini 2.5 in 2025'. Ensure the scene is rich in historical detail and atmosphere, but devoid of any human presence. Focus on the intricate details of the tea set, the newspaper's texture, and the ambient lighting typical of that period.""",
        config=dict(
            number_of_images=2,
            output_mime_type="image/jpeg",
            person_generation="ALLOW_ALL",
            aspect_ratio="9:16",
            image_size="2K",
        ),
    )

    if not result.generated_images:
        print("No images generated.")
        return

    if len(result.generated_images) != 2:
        print("Number of images generated does not match the requested number.")

    for n, generated_image in enumerate(result.generated_images):
        generated_image.image.save(f"generated_image_{n}.jpg")






def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()
    print(f"File saved to to: {file_name}")



def edit_GAIS():
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.5-flash-image"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""INSERT_INPUT_HERE"""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
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
            types.Part.from_text(text="""testeeeeeeeeeeeeeeeeeeeeeeeee"""),
        ],
        image_config=types.ImageConfig(
            aspect_ratio="9:16",
        ),
    )

    file_index = 0
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if (
            chunk.candidates is None
            or chunk.candidates[0].content is None
            or chunk.candidates[0].content.parts is None
        ):
            continue
        if chunk.candidates[0].content.parts[0].inline_data and chunk.candidates[0].content.parts[0].inline_data.data:
            file_name = f"ENTER_FILE_NAME_{file_index}"
            file_index += 1
            inline_data = chunk.candidates[0].content.parts[0].inline_data
            data_buffer = inline_data.data
            file_extension = mimetypes.guess_extension(inline_data.mime_type)
            save_binary_file(f"{file_name}{file_extension}", data_buffer)
        else:
            print(chunk.text)









############################################################
# GOOGLE AI STUDIO - MIGLIORATE
############################################################




# ----------------------------------------------------------
# Fornendo immagini:
# ----------------------------------------------------------

def edit_GAIS2(image_path):
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    mime_type, _ = mimetypes.guess_type(image_path)

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text="Analise esta imagem e gere duas versões estilizadas em cartoon"
                ),
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type
                ),
            ],
        ),
    ]

    config = types.GenerateContentConfig(
        temperature=0.75,
        response_modalities=["IMAGE", "TEXT"],
        image_config=types.ImageConfig(aspect_ratio="9:16"),
    )

    image_index = 0

    for chunk in client.models.generate_content_stream(
        model="gemini-2.5-flash-image",
        contents=contents,
        config=config,
    ):
        if not chunk.candidates:
            continue

        for part in chunk.candidates[0].content.parts:

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

#edit_GAIS2("src/image_generation/imgs/base/gen1.png")



# ----------------------------------------------------------
# Fornendo diverse immagini:
# ----------------------------------------------------------

def edit_GAIS2_multi(image_paths):
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    parts = [
        types.Part.from_text(
            text="Analise as imagens e subistitua o quadro pela monalisa"
        )
    ]

    for path in image_paths:
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
        response_modalities=["IMAGE", "TEXT"],
        image_config=types.ImageConfig(aspect_ratio="9:16"),
    )

    image_index = 0

    for chunk in client.models.generate_content_stream(
        model="gemini-2.5-flash-image",
        contents=contents,
        config=config,
    ):
        if not chunk.candidates:
            continue

        for part in chunk.candidates[0].content.parts:
            if part.text:
                print("TEXTO:", part.text)

            if part.inline_data:
                ext = mimetypes.guess_extension(part.inline_data.mime_type)
                file_name = f"output_{image_index}{ext}"
                image_index += 1

                with open(file_name, "wb") as f:
                    f.write(part.inline_data.data)

                print(f"🖼️ Imagem salva: {file_name}")

"""
edit_GAIS2_multi([
    "src/image_generation/imgs/base/gen1.png",
    "src/image_generation/imgs/base/gen2.png"
])
#"""




# ----------------------------------------------------------
# Recupero dei dati di consumo:
# ----------------------------------------------------------

def edit_GAIS3_multi(image_paths):
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    parts = [
        types.Part.from_text(
            text="Analise as imagens e substitua o quadro pela Mona Lisa"
        )
    ]

    for path in image_paths:
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
        response_modalities=["IMAGE", "TEXT"],
        image_config=types.ImageConfig(aspect_ratio="9:16"),
    )

    # 🔹 CHAMADA SEM STREAM
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

#"""
edit_GAIS3_multi([
    "src/image_generation/imgs/base/gen1.png",
    "src/image_generation/imgs/base/gen2.png"
])
#"""







# ----------------------------------------------------------
# RAGGRUPPAMENTO DELLE IMMAGINI (BASE E RIFERIMENTI):
# ----------------------------------------------------------

def edit_GAIS4_multi(base_image_path, reference_image_paths):
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    # --------------------
    # PROMPT SEMÂNTICO CLARO
    # --------------------
    parts = [
        types.Part.from_text(
            text="""
            A PRIMEIRA imagem é a IMAGEM BASE.
            As imagens seguintes são apenas REFERÊNCIAS.

            Modifique a imagem base adicionado o estilo das imagens de referencia
            """
        )
    ]

    # --------------------
    # IMAGEM BASE
    # --------------------
    with open(base_image_path, "rb") as f:
        base_bytes = f.read()

    base_mime, _ = mimetypes.guess_type(base_image_path)

    parts.append(
        types.Part.from_bytes(
            data=base_bytes,
            mime_type=base_mime
        )
    )

    # --------------------
    # IMAGENS DE REFERÊNCIA
    # --------------------
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
        response_modalities=["IMAGE", "TEXT"],
        image_config=types.ImageConfig(aspect_ratio="9:16"),
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

#"""
edit_GAIS4_multi(
    base_image_path="src/image_generation/imgs/base/gen1.png",
    reference_image_paths=[
        "src/image_generation/imgs/base/gen3.png"
        "src/image_generation/imgs/base/gen4.png"
    ]
)
#"""
