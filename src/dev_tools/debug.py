from src.tracing.tracing_core import ApplicationTracing
import json
from io import BytesIO

tracer = ApplicationTracing()
# python -m src.dev_tools.debug
# CTRL F10 Oppure CTRL + ALT + P - Avvia
# shift > - Continua fino al prossimo breakpoint

# ------------------------------------------------------------- #

from src.content_parse.module.document_parse import DocumentParse

if __name__ == "__main__":
    # Exemplo de uso
    job_id = "job_123"
    metadata = """{"user_id": "user_456"}"""

    schema = """
    {
    "summary": {
        "type": "str",
        "description": "Resumo do conteúdo do arquivo"
    }
    }
    """
    config = """
    {
    "model_provider": "OpenAI",
    "model_id": "gpt-4.1-mini",
    "max_input_tokens": 1000000,
    "debug_mode": true,
    "instructions": "Extraia dados do texto",
    "description": "Leia o texto e extraia as informações relevantes conforme o esquema definido. Retorne um JSON estruturado com os dados extraídos. Caso não encontre alguma informação, retorne null para aquele campo."
    }
    """

    with open("doc\\test files\\Endurance.pdf", "rb") as f:
        file_bytes = BytesIO(f.read())

    parser = DocumentParse(
        job_id=job_id,
        metadata=metadata,
        schema=schema,
        config=config,
        file_bytes=file_bytes,
        file_extension="pdf"
    )

    response = parser.run()

    print("\nResposta do parser:")
    print(json.dumps(response, indent=2))

