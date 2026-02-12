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

------------------------------

parse_responses:
return {
    "text_responses": ['Com certeza! Aqui está uma imagem que combina elementos das duas imagens fornecidas, mantendo um estilo artístico coeso e atraente: ', 'Com certeza! Que tal uma imagem que combine a majestade do grifo com a delicadeza e os detalhes anatômicos da borboleta, tudo no mesmo estilo de ilustração? Aqui está: '],  # Lista de respostas textuais (pode ser útil para entender o contexto da geração)
    "images": [{'mime_type': 'image/png', 'data': b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x04\x00\x00\x00\x04\x00\x08\x02\x00\x00\x00\xf0\x7f\xbc\xd4\x00\x00\x93\xa0caBX\x00\x00\x93\xa0jumb\x00\x00\x00\x1ejumdc2pa\x00\x11\x00\x10\x80\x00\x00\xaa\x008\x9bq\x03c2pa\x00\x00\x00\x176ju...\xee\xd0|\xfc\x12\x07\xbci\x1fx\xfd\xd5\xd6\xbe\x1dj\xdbx\x05\xfd\x03< \xb1;B&\xb8\x8e\x00\x00\x00\x00IEND\xaeB`\x82"}, {'mime_type': 'image/png', 'data': b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x04\x00\x00\x00\x04\x00\x08\x02\x00\x00\x00\xf0\x7f\xbc\xd4\x00\x00\x93\xa2caBX\x00\x00\x93\xa2jumb\x00\x00\x00\x1ejumdc2pa\x00\x11\x00\x10\x80\x00\x00\xaa\x008\x9bq\x03c2pa\x00\x00\x00\x176ju...\xcaF\x00\x92\x13"\x14o\xbe\xbc\xf5\x14\xb8\x1e\x88"\xda\xa1\xe1\xc3\xff?\xe2\xd3(\x06,\xe3\xf19\x00\x00\x00\x00IEND\xaeB`\x82'}],
    "generate_config": self.content_config,  # content_config geral
    "usage_metadata": [{'prompt_tokens': 587, 'output_tokens': 1320, 'total_tokens': 1907}, {'prompt_tokens': 587, 'output_tokens': 1313, 'total_tokens': 1900}]
}