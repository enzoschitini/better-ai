LINKEDIN_URL = "https://www.linkedin.com/in/enzoschitini"
PROFILE_IMAGE_PATH = "src/web_applications/utils/images/profile.jpg"

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
            "description": "Produza conteúdo alinhado à marca com agilidade e consistência. Treinada com mais de 50 documentos do Grupo O Boticário, a IA entende a identidade da marca e mantém o padrão em cada texto gerado.",
            "image": "src/web_applications/pages/content_generator/images/logo_oboticario.jpg",
        }
    },
    "natura": {
        "name": "Natura",
        "description": "Base de dados da Natura &Co.",
        "link": "https://www.natura.com.br/",
        "filter_search": {"collection_id": ["natura"]},
        "header": {
            "title": "Natura · IA de Conteúdo",
            "description": "Produza conteúdo alinhado à marca com agilidade e consistência. Treinada com mais de 50 documentos da Natura &Co., a IA entende a identidade da marca e mantém o padrão em cada texto gerado.",
            "image": "https://www.natura.com.br/static/version1677159600/frontend/Natura/base/pt_BR/images/logo-natura.svg",
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
    "google": {
        "name": "gemini-2.5-pro",
        "description": "Modelo de linguagem da Google.",
        "id": "gemini-2.5-pro",
    },
    "groq": {
        "name": "llama-3.3-70b-versatile",
        "description": "Modelo de linguagem da Groq.",
        "id": "llama-3.3-70b-versatile",
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