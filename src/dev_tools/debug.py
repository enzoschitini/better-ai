from src.tracing.tracing_core import ApplicationTracing

tracer = ApplicationTracing()
# python -m src.dev_tools.debug
# CTRL F10 Oppure CTRL + ALT + P - Avvia
# shift > - Continua fino al prossimo breakpoint

# ------------------------------------------------------------- #

import json
from src.vector_store.pinecone.embedding import PineconeEmbedding
from src.vector_store.pinecone.client import PineconeClient

pine_client = PineconeClient(
    index_name="backai-vectorstore",
    main_namespace="embedding_file",
)

service = PineconeEmbedding(pine_client)
response = service.generate_vectors(
    text="""
Era uma vez uma cidade onde ninguém sonhava.

Não porque fosse proibido, nem porque faltasse imaginação — simplesmente, os sonhos tinham desaparecido. As pessoas dormiam, acordavam e seguiam suas rotinas perfeitamente organizadas, como relógios que nunca atrasam. Não havia pesadelos, mas também não havia aquela sensação estranha de acordar com o coração acelerado por algo impossível de explicar.

Exceto por um garoto chamado Theo.

Theo começou a perceber que algo estava errado quando acordou certa manhã com a nítida lembrança de ter voado. Não era como imaginar — ele sentiu o vento, viu as ruas lá embaixo, pequenas como brinquedos. Quando contou aos pais, eles trocaram olhares desconfortáveis.

— Foi só impressão — disseram.

Mas não foi.

Na noite seguinte, Theo sonhou de novo. E na outra também. Logo, percebeu um padrão: seus sonhos estavam ficando mais vívidos… e mais reais.

Curioso, ele começou a anotá-los em um caderno escondido debaixo da cama. Montanhas flutuantes, mares que brilhavam no escuro, pessoas que falavam em enigmas. Um mundo inteiro parecia existir dentro de sua cabeça — um mundo que ninguém mais podia acessar.

Até que, em um dos sonhos, algo diferente aconteceu.

Uma figura apareceu.

Não tinha rosto definido, mas tinha presença. Ficava parada, observando Theo como se o estivesse esperando.

— Você demorou — disse a figura.

Theo, mesmo dentro do sonho, sentiu um arrepio.

— Demorei… pra quê?

— Pra lembrar.

Na manhã seguinte, Theo acordou com uma certeza estranha: seus sonhos não eram apenas sonhos. Eram memórias.

Determinando a descobrir a verdade, ele começou a prestar atenção nas pequenas falhas da cidade. Pessoas repetindo frases, relógios que nunca mudavam, dias que pareciam cópias uns dos outros. Era como se tudo estivesse preso em um ciclo invisível.

Então veio o estalo.

Se ninguém sonhava… talvez alguém tivesse tirado isso deles.

Naquela noite, Theo voltou a encontrar a figura.

— Quem fez isso com a gente? — perguntou, sem hesitar.

A figura se aproximou.

— Vocês fizeram.

O silêncio pesou.

— As pessoas tiveram medo — continuou. — Sonhos trazem caos. Emoções. Dúvidas. Então escolheram a ordem. Escolheram esquecer.

— E eu?

— Você não escolheu.

Theo ficou em silêncio por um tempo.

— Então… eu posso trazer de volta?

A figura pareceu sorrir — ou algo próximo disso.

— Pode tentar.

Na manhã seguinte, Theo fez algo simples: contou um sonho para um colega na escola.

No começo, o garoto riu. Disse que era estranho. Mas, naquele mesmo dia, algo mudou. Ele ficou distraído. Olhava para o nada como se estivesse tentando lembrar de algo distante.

Na noite seguinte… ele sonhou.

Pouco a pouco, Theo começou a espalhar histórias. Não como verdades, mas como possibilidades. E, como uma faísca em palha seca, os sonhos começaram a voltar.

Primeiro raros. Depois confusos. Depois intensos.

E com eles vieram risos inesperados, lágrimas sem motivo claro, ideias novas, perguntas perigosas.

A cidade deixou de ser perfeita.

Mas voltou a ser viva.

E quanto à figura nos sonhos?

Ela nunca mais apareceu.

Porque, de certa forma… nunca foi necessária.
""",
    metadata={"file_id": "test_file_12345"},
    save_global=True
)
print(json.dumps(response, indent=4, default=str))
