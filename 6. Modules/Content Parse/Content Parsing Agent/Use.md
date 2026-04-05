# Use `ContentParsingAgent`

### Imports:

```python
import json
from src.content_parse.content_parsing_agent import ContentParsingAgent
```

### Input Text:

```python
input_text = """
Title: The Future of AI
Author: John Doe
Code: 

Artificial Intelligence is evolving rapidly. Companies are investing heavily
in automation and machine learning to improve efficiency and decision-making.

Enzo: Is a data scientist and has 5 years of experience
Laura: Is a software engineer and has 3 years of experience
Marico: Is a product manager and has 7 years of experience.
"""
```

### Schema:

```python
output_data = {
    "title": {
        "type": "str",
        "description": "Title of the content",
        "example": "The Future of AI"
    },
    "author": {
        "type": "str",
        "description": "Author of the content",
        "example": "John Doe"
    },
    "summary": {
        "type": "str",
        "required": False,
        "description": "Short summary of the text",
        "example": "Artificial Intelligence is evolving rapidly. Companies are investing heavily in automation and machine learning to improve efficiency and decision-making."
    },
    "code": {
        "type": "str",
        "description": "Code snippet extracted from the text",
        "required": True
    },
    "names": {
        "type": "list",
        "description": "List of names mentioned in the text",
        "items": {
            "type": "str",
            "description": "A person's name mentioned in the text"
        }
    },

    "peoples": {
        "type": "list",
        "description": "List of people with structured details extracted from the text",
        "max_length": 1,
        "items": {
            "type": "object",
            "description": "A person mentioned in the text",
            "properties": {
                "name": {
                    "type": "str",
                    "description": "Full name of the person"
                },
                "experience": {
                    "type": "str",
                    "description": "Years of experience or expertise level"
                },
                "profession": {
                    "type": "str",
                    "description": "Profession or role of the person"
                }
            }
        }
    }
}
```

### Config:

```python
config_data = {
    "model_provider": "OpenAI",
    "model_id": "gpt-4.1-mini",
    "debug_mode": True,
    "instructions": "Extraia dados do texto",
    "description": "Leia o texto e extraia as informações relevantes conforme o esquema definido. Retorne um JSON estruturado com os dados extraídos. Caso não encontre alguma informação, retorne null para aquele campo."
}
```

### Run Parse:

```python
if __name__ == "__main__":
    agent_parser = ContentParsingAgent(
        input_data=input_data,
        output_data=output_schema,
        config_data=config_data
    )
    content_parsed = agent_parser.run_agent()
    response = agent_parser.format_response(content_parsed)
    print(json.dumps(response, indent=4, ensure_ascii=False))

# python -m src.content_parse.content_parsing_agent
```
