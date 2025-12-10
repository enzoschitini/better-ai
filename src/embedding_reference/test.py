"""
https://knowledge.labflix.io/docs/21d75dca2eec7b02080327f40220e20d.pdf
https://knowledge.labflix.io/docs/f0cd98836768d42b7d904f117151cf39.csv
https://knowledge.labflix.io/docs/c4a07e949166f216521ccf984065a02b.xlsx
https://knowledge.labflix.io/docs/d410a32441569ec53766cec928b72be9.pptx
https://knowledge.labflix.io/docs/fe900e4b998f88062158587683c8dc8d.docx
https://knowledge.labflix.io/docs/485a21ab2a2fccfbc7fa02cf7f4ad5ae.html

https://knowledge.labflix.io/images/bc6d3772abe0d6b30c6b4ed373596686.png
https://knowledge.labflix.io/audios/186b2fbdd765d41db6326560c193ba7b.mp3
docs/d4184190c5948bc2a782de50cbcb093b.csv
"""

sqs_message = {
    "jobId": "asdwjfkdjfsdklfssssssflaur6565",
    "fileId": "21d75dca2eec7b02080327f40220e20dxx2.pdf",
    "fileUrl": "docs/21d75dca2eec7b02080327f40220e20d.pdf",
    "metadata": {
        "id_collection": "id_collection_01",
        "id_series": "id_series_01",
        "id_client": "id_client_01",
        "id_user": "id_user_01",
        "id_workspace": "id_workspace_01",

        "st_name": "nome_do_arquivo.pdf",
        "nm_resource_size": 102400,        
        "fk_knowledgetype": "document",
        "st_process_status": None,
        "js_metadata": None
    }
}

# docker ps
# docker run -d --name redis -p 6379:6379 redis
# docker stop redis
# docker rm redis
# python -m src.knowledge_base.test

from src.knowledge_base.embedding_module import EmbeddingFile
embedding = EmbeddingFile(sqs_message)
result = embedding.run()

import json
print(json.dumps(result, indent=4, ensure_ascii=False))




"""
{'response': {'file_content': 'A imagem é uma ilustração 3D vibrante e colorida, em estilo cartoon, que retrata um jovem astronauta celebrando um aniversário em um cenário extraterrestre.\n\nNo centro da composição, um boneco de criança, com traços arredondados e expressivos, veste um traje espacial branco detalhado com partes azuis (capacete, luvas e botas) e alguns detalhes em laranja e preto. O capacete azul possui um visor transparente que revela o rosto sorridente da criança, com olhos grandes e escuros, boca aberta em um sorriso alegre e cabelos castanhos curtos. Há protetores auriculares ou detalhes decorativos em laranja nas laterais do capacete.\n\nO astronauta está em pé, olhando para a frente, e segura na mão direita um objeto que parece ser um pequeno espeto com uma bandeirinha vermelha e um adorno branco e azul. Ao seu lado direito (esquerda do observador), há um bolo de aniversário de dois andares, com cobertura amarela e calda vermelha escorrendo pelas laterais. O bolo está sobre um suporte branco e é decorado com várias frutas vermelhas (morangos ou cerejas) e pequenos pirulitos em formato de coração e outros em formato circular, alguns dos quais parecem ter o número "1" ou outros símbolos de festa.\n\nO cenário é uma paisagem de tom alaranjado, semelhante à superfície de Marte, com formações rochosas arredondadas e crateras suaves, sugerindo um terreno desértico. Pequenas pedras e detritos estão espalhados pelo solo. O céu é um gradiente que vai do azul escuro no canto superior esquerdo para um laranja-amarelado brilhante perto do horizonte, salpicado por numerosas estrelas brancas.\n\nNo fundo e no alto, diversos corpos celestes e objetos flutuam:\n*   No canto superior esquerdo, um grande planeta laranja com um anel proeminente ao redor, similar a Saturno.\n*   No canto superior direito, um grande planeta azul-claro, parcialmente visível.\n*   Pelo céu, há vários planetas menores de diferentes cores (laranja listrado, verde, pequenos pontos vermelhos e esferas marrons), além de alguns objetos geométricos triangulares vermelhos.\n*   Na parte inferior direita, no terreno, há um objeto esférico com camadas brancas e laranja, que lembra um macaron gigante ou um corpo planetário estilizado.\n\nA imagem transmite uma atmosfera de alegria, aventura e fantasia espacial, com cores vibrantes e um estilo de ilustração polido em 3D.',
  'usage_metadata': {'prompt_token_count': 1943,
   'candidates_token_count': 521,
   'total_token_count': 3917}}}
"""
