from fastapi import UploadFile
import json

from src.embedding.embedding_module import ContentExtractorService, FileService
from src.text_parse.text_parse import GenericTextExtractor
from src.text_parse.cost import LLMCostCalculator


def calc_cost_informations(model: str, schema: dict, scraper: str, result: dict):
    import json

    input = str(schema) + str(scraper)
    output = str(result)

    calculator = LLMCostCalculator(model=model)

    cost_informations = calculator.calculate(
        input_text=input,
        output_text=output
    )

    return cost_informations



class TextParserModule:
    def __init__(self, payload: dict, file: UploadFile):
        
        self.job_id = payload.get("job_id", "")
        self.metadata = payload.get("metadata", {})
        self.schema = payload.get("schema", {})

        self.payload = payload
        self.file = file

    async def execute(self) -> dict:
        import time
        start_time = time.time()

        file_name, file_extension, file_bytes = await FileService.load(self.file)

        scraper = ContentExtractorService.extract(file_bytes, file_extension)
        scraper = scraper["response"]
        print(scraper[:100])

        extractor = GenericTextExtractor(self.payload["schema"])
        #parse = extractor.extract(scraper)
        parse = {
            "titolo": "Governo anuncia novas medidas econômicas",
            "descricao": "O governo implementou uma série de medidas para estimular a economia nacional.",
            "informacoes_chave": [
                "Medidas incluem redução de impostos e incentivos para pequenas empresas.",
                "Foco em inovação tecnológica e sustentabilidade."
            ]
        }

        cost_informations = calc_cost_informations(model="gpt-4o-mini", 
                                                   schema=self.schema, scraper=scraper, 
                                                   result=parse)


        end_time = time.time()
        print(f"Tempo de execução: {end_time - start_time:.2f} segundos")

        result = {
            "job_id": self.job_id,
            "file_name": file_name,
            "cost_informations": cost_informations,
            "response": parse
        }

        print(f"\n{json.dumps(result, indent=2, ensure_ascii=False)}")

        return result


# python -m src.text_parse.extract