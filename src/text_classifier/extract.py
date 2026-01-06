import asyncio
from io import BytesIO
from fastapi import UploadFile
import yaml
import json

# ==============================
# Embedding Module
# ==============================

from src.embedding.embedding_module import ContentExtractorService, FileService
from src.text_classifier.text_classifier import GenericTextExtractor
from src.chat.tokens_calculator.cost_calculator import CostCalculator

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





class TextParserModule:
    def __init__(self, payload: dict, file: UploadFile):
        self.payload = payload
        self.file = file

    async def execute(self) -> dict:
        # 1. Load file
        file_name, file_extension, file_bytes = await FileService.load(self.file)

        import time

        start_time = time.time()

        extractor = GenericTextExtractor(self.payload["schema"])

        # 2. Extract content
        scraper = ContentExtractorService.extract(file_bytes, file_extension)
        scraper = scraper["response"]

        #resultado = extractor.extract(scraper)
        resultado = {
            "titolo": "Governo anuncia novas medidas econômicas",
            "descricao": "O governo implementou uma série de medidas para estimular a economia nacional.",
            "informacoes_chave": [
                "Medidas incluem redução de impostos e incentivos para pequenas empresas.",
                "Foco em inovação tecnológica e sustentabilidade."
            ]
        }

        # Costo
        cost_informations = {
            "llm_model": {
                "name": "gpt-4o-mini",
                "input_rate_per_1k_tokens_usd": 0.001,
                "output_rate_per_1k_tokens_usd": 0.004
            },

            "tokens": {
                "input_tokens": 1500,
                "output_tokens": 500,
                "total_tokens": 2000
            },
            
            "cost": {
                "usd": {
                    "input_cost_usd": "0.001500",
                    "output_cost_usd": "0.000500",
                    "total_cost_usd": "0.002000"
                }
            },

            "rates": {
                "EUR": 0.85,
                "BRL": 4.50
            }
        }






        """
        # Salvar resultado em JSON
        with open(f"src/text_classifier/output_{file_name.replace(f'.{file_extension}', '')}.json", "w", encoding="utf-8") as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)

        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        """



        end_time = time.time()
        print(f"Tempo de execução: {end_time - start_time:.2f} segundos")









async def run_test():
    file_path = "src/text_classifier/txt_examples/g1.txt"

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



# python -m src.text_classifier.extract




