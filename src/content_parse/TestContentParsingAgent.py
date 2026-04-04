import json
from src.content_parse.content_parsing_agent import ContentParsingAgent

text = """
Este produto foi desenvolvido para oferecer praticidade e eficiência no dia a dia, combinando design moderno com alta funcionalidade. Pensado para atender às necessidades de diferentes perfis de usuários, ele se destaca pela facilidade de uso e pela qualidade dos materiais utilizados em sua fabricação. Cada detalhe foi cuidadosamente planejado para garantir uma experiência intuitiva, tornando tarefas rotineiras mais simples e agradáveis.

Além disso, o produto apresenta excelente durabilidade e desempenho consistente, mesmo em condições de uso frequente. Seu custo-benefício é um dos grandes atrativos, proporcionando uma solução confiável sem comprometer o orçamento. Seja para uso pessoal ou profissional, trata-se de uma escolha inteligente para quem busca inovação, praticidade e resultados satisfatórios.
"""

input_data = {
    "product_review": text,
    "task": "Nas key_words identifique pelo menos 5"
}

output_schema = {
  "product_description": {
    "type": "str",
    "description": "Descrição geral do produto apresentada no texto"
  },
  "main_benefit": {
    "type": "str",
    "description": "Principal benefício ou proposta de valor do produto"
  },
  "key_features": {
    "type": "str",
    "description": "Principais características mencionadas"
  },
  "target_use": {
    "type": "str",
    "description": "Para que tipo de uso ou situação o produto é indicado"
  },
  "value_proposition": {
    "type": "str",
    "description": "Resumo do porquê o produto é uma boa escolha"
  }
}



config_data = {
    "model_provider": "OpenAI",
    "model_id": "gpt-4.1-mini",
    "debug_mode": True,
    "instructions": "Extraia dados do texto",
    "description": "Leia o texto e extraia as informações relevantes conforme o esquema definido. Retorne um JSON estruturado com os dados extraídos. Caso não encontre alguma informação, retorne null para aquele campo."
}

"""
    "model_provider": "Groq",
    "model_id": "llama-3.3-70b-versatile",
    "model_provider": "OpenAI",
    "model_id": "gpt-4.1-mini",

# criar venv (se ainda não tiver)
python -m venv venv

# ativar
venv\Scripts\activate

# instalar tudo
pip install -r requirements.txt

# rodar o projeto
python -m uvicorn app.main:app --reload

"""


if __name__ == "__main__":
    agent_parser = ContentParsingAgent(
        input_data=input_data,
        output_data=output_schema,
        config_data=config_data
    )
    content_parsed = agent_parser.run_agent()
    response = agent_parser.format_response(content_parsed)
    print(json.dumps(response, indent=4, ensure_ascii=False))


# python -m src.content_parse.TestContentParsingAgent