import asyncio
from fastapi import UploadFile
from src.text_parse.extract import TextParserModule

schema = [
  {
    "name": "titolo",
    "type": "str",
    "title": "Títolo da notícia",
    "description": "Títolo principal da notícia",
    "examples": [
      "Governo anuncia novas medidas econômicas",
      "Descoberta científica revoluciona tratamento de doenças"
    ]
  },
  {
    "name": "descricao",
    "type": "str",
    "title": "Descrição da notícia",
    "description": "Resumo breve do conteúdo da notícia",
    "examples": [
      "O governo implementou uma série de medidas para estimular a economia nacional.",
      "Cientistas desenvolveram uma nova técnica que promete melhorar significativamente o tratamento de várias doenças."
    ]
  },
  {
    "name": "informacoes_chave",
    "type": "list",
    "title": "Informações chave",
    "description": "Lista de pontos importantes abordados na notícia",
    "items": {
      "type": "str"
    },
    "examples": [
      "Medidas incluem redução de impostos e incentivos para pequenas empresas.",
      "Nova técnica utiliza nanotecnologia para direcionar medicamentos diretamente às células afetadas."
    ]
  }
]

payload = {
    "client_id": "client_123",
    "job_id": "test_job_001",
    "metadata": None,
    "schema": schema
}


async def run_test():
    file_path = "src/text_parse/txt_examples/g1.txt"

    with open(file_path, "rb") as f:
        upload_file = UploadFile(
            filename="g1.txt",
            file=f
        )

        module = TextParserModule(
            payload=payload,
            file=upload_file
        )

        result = await module.execute()


if __name__ == "__main__":
    asyncio.run(run_test())






# python -m src.text_parse.test

"""
# Salvar resultado em JSON
with open(f"src/text_parse/output_{file_name.replace(f'.{file_extension}', '')}.json", "w", encoding="utf-8") as f:
    json.dump(resultado, f, indent=2, ensure_ascii=False)

print(json.dumps(resultado, indent=2, ensure_ascii=False))
"""



