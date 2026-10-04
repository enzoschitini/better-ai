"""Fonte única da estrutura da documentação.

Este arquivo é DECLARATIVO: literais e os dois helpers abaixo. Sem lógica,
sem imports, sem condicionais. Quem precisa da árvore como dado consome o
`dist/<lang>/structure.json`, gerado em todo build.

O que mora aqui: a árvore, a ordem, os slugs, os ícones das áreas e os
títulos de área por idioma.

O que NÃO mora aqui: títulos de página por idioma, resumos, datas, status de
tradução e conteúdo. Título de página vem do `data-title` do fragmento;
status de tradução é derivado da existência do arquivo.

Transliterado de `AREAS` em doc/site-prototype/index.html (~linha 1446).
Os 61 ids gerados daqui têm de bater com os do protótipo.
"""


def page(title, *, slug=None, empty=False):
    """Uma página folha.

    title  rótulo no menu lateral (decisão: o menu usa este nome, não o
           data-title do fragmento, para preservar o menu aprovado)
    slug   sobrescreve o slug derivado do título
    empty  True = documento ainda não escrito. Não se espera fragmento, e a
           página renderiza o bloco `.empty` com badge no menu.
    """
    return {"t": title, "slug": slug, "empty": empty}


def folder(title, kids, *, slug=None):
    """Um nível intermediário. Não tem página própria."""
    return {"t": title, "slug": slug, "kids": kids}


# Idiomas construídos. O primeiro é o padrão e o fallback.
LANGS = ["pt", "en", "it"]
DEFAULT_LANG = "pt"

AREAS = [
    {
        "t": "Getting Started",
        "icon": "bolt",
        "slug": "getting-started",
        "titles": {"pt": "Getting Started", "en": "Getting Started", "it": "Getting Started"},
        "loose": {"pt": "Primeiros passos", "en": "First steps", "it": "Primi passi"},
        "about": {
            "pt": "Instalação, dependências e licença. Do clone ao primeiro request.",
            "en": "Installation, dependencies and license. From clone to first request.",
            "it": "Installazione, dipendenze e licenza. Dal clone alla prima request.",
        },
        "kids": [
            page("Quickstart"),
            page("Dependences"),
            page("Licence"),
        ],
    },
    {
        "t": "Modules",
        "icon": "boxes",
        "slug": "modules",
        "titles": {"pt": "Modules", "en": "Modules", "it": "Modules"},
        "about": {
            "pt": "Os serviços de IA da plataforma: agentes, parsing de documentos, deep research, embeddings, imagens, Pinecone e a API.",
            "en": "The platform's AI services: agents, document parsing, deep research, embeddings, images, Pinecone and the API.",
            "it": "I servizi di IA della piattaforma: agenti, parsing di documenti, deep research, embeddings, immagini, Pinecone e l'API.",
        },
        "kids": [
            folder("Agents", [
                folder("Utils", [
                    page("Database"),
                    page("Model Gateway"),
                ]),
            ]),
            folder("Content Parse", [
                folder("Content Parsing Agent", [
                    page("Documentation"),
                    page("Use"),
                ]),
                page("Document Parse"),
                page("Field Metadata Parser"),
                page("Generate Pydantic Schema"),
                page("Json To Pydantic"),
            ]),
            folder("Deep Research", [
                folder("Tavily Research", [
                    page("Context Builder", empty=True),
                    page("Tavily Core", empty=True),
                ]),
            ]),
            folder("Embedding", [
                page("Delete Embeddings"),
                page("Embedding Module"),
                folder("Local Dynamic Embedding", [
                    page("Documentation"),
                    page("Use"),
                ]),
            ]),
            # Área inteira ainda sem conteúdo escrito.
            folder("Image Generation", [
                page("Module", empty=True),
                page("Image Generator Service", empty=True),
                folder("Cost Calculator", [
                    page("Cost Calculator", empty=True),
                    page("Pricing Table", empty=True),
                ]),
                folder("Utils", [
                    page("Config", empty=True),
                    page("Gemini Client", empty=True),
                    page("Params Validator", empty=True),
                    page("Payload Builder", empty=True),
                ]),
            ]),
            folder("Pinecone Vector Store", [
                page("Pinecone Client"),
                page("Pinecone Retriever"),
                page("Pinecone Vector Service"),
                page("Retrieval Manager"),
            ]),
            folder("Web Service Network", [
                page("Curl Compiler"),
                page("Web Service API"),
                page("Web Service Network - API"),
            ]),
        ],
    },
    {
        "t": "Internal Source Code",
        "icon": "code",
        "slug": "internal-source-code",
        "titles": {"pt": "Internal Source Code", "en": "Internal Source Code", "it": "Internal Source Code"},
        "loose": {"pt": "Geral", "en": "General", "it": "Generale"},
        "about": {
            "pt": "A infraestrutura por baixo: tracing, bancos de dados, storage, custo por token e utilitários.",
            "en": "The infrastructure underneath: tracing, databases, storage, token cost and utilities.",
            "it": "L'infrastruttura sottostante: tracing, database, storage, costo per token e utilità.",
        },
        "kids": [
            page("AgnoUI"),
            folder("Application Tracing", [
                page("Logger Engine"),
                page("Payload Builder"),
                page("Tracing Core"),
                page("Use", empty=True),
            ]),
            folder("Database", [
                folder("No SQL", [
                    page("Local Manage"),
                    page("Mongo Manager"),
                    page("Router"),
                ]),
                folder("SQL", [
                    page("Supabase Database"),
                ]),
            ]),
            folder("Storage", [
                page("Storage Menage Repository"),  # sic: typo preservado da origem
                folder("Supabase", [
                    page("Storage Menager"),  # sic: typo preservado da origem
                ]),
            ]),
            folder("Token Calculate", [
                folder("Exchange Rate", [
                    page("BCB Exchange Rate Service"),
                    page("Exchange Rate Service"),
                ]),
                page("Model Pricing"),
                page("Token Counter"),
            ]),
            folder("Utils", [
                folder("Load Request File", [
                    page("Documentation"),
                    page("Use"),
                ]),
                page("Loader Files"),
                page("Unique ID Factory"),
            ]),
            folder("Vector Store", [
                page("Pinecone Client"),
                page("Pinecone Embedding"),
                page("Pinecone Retriever"),
            ]),
        ],
    },
    {
        "t": "Streamlit Applications",
        "icon": "layout",
        "slug": "streamlit-applications",
        "titles": {"pt": "Streamlit Applications", "en": "Streamlit Applications", "it": "Streamlit Applications"},
        "loose": {"pt": "Aplicações", "en": "Applications", "it": "Applicazioni"},
        "about": {
            "pt": "Acquarello e Content Generator, as duas aplicações que rodam sobre a plataforma.",
            "en": "Acquarello and Content Generator, the two applications running on the platform.",
            "it": "Acquarello e Content Generator, le due applicazioni che girano sulla piattaforma.",
        },
        "kids": [
            page("Acquarello"),
            page("Content Generator"),
        ],
    },
]

# Sugestões na busca vazia.
POPULAR = [
    "getting-started/quickstart",
    "modules/agents/utils/model-gateway",
    "modules/web-service-network/web-service-network-api",
    "streamlit-applications/acquarello",
]
