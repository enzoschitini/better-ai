from dataclasses import dataclass, field

@dataclass
class Config:
    model_provider: str = "OpenAI"
    # Models: OpenAIChat(id="gpt-4.1-mini"), Groq(id="llama-3.3-70b-versatile"),
    model_id: str = "gpt-4.1-mini"
    max_input_tokens: int = 1000000
    debug_mode: bool = True

    # Come lo fai
    instructions: str = """
    Extraia dados do texto
    """

    # Cosa sei
    description: str = """
    Leia o texto e extraia as informações relevantes conforme o esquema definido. Retorne um JSON estruturado com os dados extraídos.
    Caso não encontre alguma informação, retorne null para aquele campo.
    """


@dataclass
class DocumentParseConfig:
    default_config: dict = field(default_factory=lambda: {
        "model_provider": "OpenAI",
        "model_id": "gpt-4.1-mini",
        "max_input_tokens": 1000000,
        "debug_mode": False,
        "instructions": "Extraia dados do texto",
        "description": (
            "Leia o texto e extraia as informações relevantes conforme o esquema definido. "
            "Retorne um JSON estruturado com os dados extraídos. "
            "Caso não encontre alguma informação, retorne null para aquele campo."
        )
    })

    database_name: str = "process_informations"
    collection_name: str = "document_parse"
