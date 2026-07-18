from dataclasses import dataclass

DEFAULT_CONTENT_CONFIG = {
    "model": "gemini-2.5-flash-image",
    "temperature": 0.75,
    "top_p": 0.85,
    "max_output_tokens": 1024,
    "aspect_ratio": "1:1",
    "number_of_images": 1
}


STYLE_MAPPING = {
    "Aquarela": {
        "style_en": "watercolor",
        "description": "Pinceladas suaves, cores fluidas e acabamento artistico organico.",
    },
    "Cartoon": {
        "style_en": "cartoon",
        "description": "Contornos marcados, cores vibrantes e visual divertido e estilizado.",
    },
    "Anime": {
        "style_en": "anime",
        "description": "Linhas definidas, olhos expressivos e proporções estilizadas tipicas da animacao japonesa.",
    },
    "Line Art": {
        "style_en": "lineart",
        "description": "Contornos limpos e precisos, com pouco ou nenhum preenchimento de cor, enfatizando a qualidade da linha.",
    },
    "Pop Art": {
        "style_en": "popart",
        "description": "Cores ousadas, padroes repetitivos e elementos graficos inspirados na cultura popular.",
    },
    "Foto Realista": {
        "style_en": "photorealistic",
        "description": "Detalhes realistas, iluminacao natural e texturas convincentes para uma representacao fiel da realidade.",
    },
}
