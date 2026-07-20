DATABASES = {
    "oboticario": {
        "name": "Oboticário",
        "description": "Base de dados do Grupo O Boticário.",
        "link": "https://www.grupoboticario.com.br/",
        "header": {
            "title": "OBoticário · IA de Conteúdo",
            "description": "Produza conteúdo alinhado à marca com agilidade e consistência. Treinada com mais de 50 documentos do Grupo O Boticário, nossa IA entende a identidade da marca e mantém o padrão em cada texto gerado.",
            "image": "src/web_applications/pages/content_generator/images/logo_oboticario.jpg",
        }
    },
    "natura": {
        "name": "Natura",
        "description": "Base de dados da Natura &Co.",
        "link": "https://www.natura.com.br/",
        "header": {
            "title": "Natura · IA de Conteúdo",
            "description": "Produza conteúdo alinhado à marca com agilidade e consistência. Treinada com mais de 50 documentos da Natura &Co., nossa IA entende a identidade da marca e mantém o padrão em cada texto gerado.",
            "image": "https://www.natura.com.br/static/version1677159600/frontend/Natura/base/pt_BR/images/logo-natura.svg",
        }
    },
}

LLM_MODELS = {
    "openai": {
        "name": "OpenAI",
        "description": "Modelo de linguagem da OpenAI.",
        "id": "gpt-4",
    },
    "anthropic": {
        "name": "Claude",
        "description": "Modelo de linguagem da Anthropic.",
        "id": "claude-v1",
    },
}