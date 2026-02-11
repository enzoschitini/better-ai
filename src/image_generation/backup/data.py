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

METADATA DE USO

if response.usage_metadata:

usage_metadata = {'prompt_tokens': 526, 'output_tokens': 12, 'total_tokens': 538}
