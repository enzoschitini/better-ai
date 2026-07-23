LINKEDIN_URL = "https://www.linkedin.com/in/enzoschitini"
PROFILE_IMAGE_PATH = "src/web_applications/utils/images/profile.jpg"
RAG_IMAGE_PATH = "src/web_applications/pages/content_generator/images/rag.png"

DEFAULT_OBJECTIVE = (
    "Gerar artigos de blog voltados para o topo do funil, com o objetivo de "
    "atrair e educar potenciais clientes. O conteúdo deve responder a dúvidas "
    "comuns do público-alvo e posicionar a marca como referência no assunto."
)

DATABASES = {
    "oboticario": {
        "name": "Oboticário",
        "description": "Base de dados do Grupo O Boticário.",
        "link": "https://www.grupoboticario.com.br/",
        "filter_search": {"collection_id": ["oboticario"]},
        "header": {
            "title": "OBoticário · IA de Conteúdo",
            "description": "Produza conteúdo alinhado à marca com agilidade e consistência. Treinada com documentos do Grupo O Boticário, a IA entende a identidade da marca e mantém o padrão em cada texto gerado.",
            "image": "src/web_applications/pages/content_generator/images/logo_oboticario.jpg",
        }
    },
}

LLM_MODELS = {
    "openai": {
        "name": "gpt-4.1-mini",
        "description": "Modelo de linguagem da OpenAI.",
        "id": "gpt-4.1-mini",
    },
    "anthropic_1": {
        "name": "claude-opus-4-5",
        "description": "Modelo de linguagem da Anthropic.",
        "id": "claude-opus-4-5",
    },
    "anthropic_2": {
        "name": "claude-sonnet-4-6",
        "description": "Modelo de linguagem da Anthropic.",
        "id": "claude-sonnet-4-6",
    },
}

DEFAULT_LINGUAGES = {
    "pt": {
        "name": "Português",
        "prompt": "Generate content in Portuguese.",
        "id": "pt",
    },
    "livre": {
        "name": "Livre",
        "prompt": "Generate content in any language.",
        "id": "livre",
    },
    "en": {
        "name": "Inglês",
        "prompt": "Generate content in English.",
        "id": "en",
    },
    "es": {
        "name": "Espanhol",
        "prompt": "Generate content in Spanish.",
        "id": "es",
    },
    "it": {
        "name": "Italiano",
        "prompt": "Generate content in Italian.",
        "id": "it",
    },
    "fr": {
        "name": "Francês",
        "prompt": "Generate content in French.",
        "id": "fr",
    },
    "de": {
        "name": "Alemão",
        "prompt": "Generate content in German.",
        "id": "de",
    },
}

DEFAULT_OBJECTIVE = (
    "Gerar artigos de blog voltados para o topo do funil, com o objetivo de "
    "atrair e educar potenciais clientes. O conteúdo deve responder a dúvidas "
    "comuns do público-alvo, posicionar a marca como referência no assunto e "
    "incentivar o leitor a avançar na jornada de compra.\n\n"
    "Público-alvo: pequenos e médios empreendedores.\n"
    "Tom de voz: informativo, acessível e próximo.\n"
    "Objetivo de negócio: aumentar tráfego orgânico e geração de leads."
)

DEFAULT_REQUIREMENTS = (
    "- Utilizar subtítulos (H2 e H3) para organizar o conteúdo.\n"
    "- Evitar jargões técnicos; explicar termos quando necessário.\n"
    "- Incluir uma introdução que contextualize o problema do leitor.\n"
    "- Finalizar com uma chamada para ação (CTA) clara.\n"
    "- Não mencionar marcas concorrentes.\n"
    "- Manter frases curtas e parágrafos objetivos."
)