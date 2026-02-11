parts = [
    Part(
        text="Gere uma imagem seguindo o estilo dessas"
    ),
    Part(
        inline_data=Blob(
            data=b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00...\xff...",
            mime_type="image/jpeg",
        )
    ),
    Part(
        inline_data=Blob(
            data=b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00...\xff...",
            mime_type="image/jpeg",
        )
    ),
]



contents = [
    Content(
        parts=[
            Part(
                text="Gere uma imagem seguindo o estilo dessas"
            ),
            Part(
                inline_data=Blob(
                    data=b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00...\xff...",
                    mime_type="image/jpeg",
                )
            ),
        ],
        role="user",
    )
]


config = GenerateContentConfig(
    image_config=ImageConfig(
        aspect_ratio="9:16",
    ),
    max_output_tokens=1024,
    response_modalities=[
        "IMAGE",
        "TEXT",
    ],
    temperature=0.75,
    top_p=0.85,
)

--------------------------------------------------------------


PARSE DA RESPOSTA

for part in response.candidates[0].content.parts:

part = Part(
  text='Com certeza! Qual animal você gostaria de ver nesse estilo?'
)

images = [{'mime_type': 'image/png', 'data': b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x03\x00\x00\x00\x05@\x08\x02\x00\x00\x00pk\xa8\x8f\x00\x00\x92\xfccaBX\x00\x00\x92\xfcjumb\x00\x00\x00\x1ejumdc2pa\x00\x11\x00\x10\x80\x00\x00\xaa\x008\x9bq\x03c2pa\x00\x00\x00\x176ju...b\xe8\xedq33\xf5\x90b@\xa5\xdf\xe2\xce\xad\xda\x90fd\xfc\xff\x01\xf8H\xda\n\xc6j\\\xa8\x00\x00\x00\x00IEND\xaeB`\x82'}]


METADATA DE USO

if response.usage_metadata:

usage_metadata = {'prompt_tokens': 526, 'output_tokens': 12, 'total_tokens': 538}
