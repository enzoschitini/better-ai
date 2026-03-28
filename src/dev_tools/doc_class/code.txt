from fastapi import UploadFile

from src.embedding.embedding_module import ContentExtractorService, FileService
from src.text_parse.langchain_parse import GenericTextExtractor
from src.text_parse.cost import LLMCostCalculator


class TextParserModule:
    def __init__(self, payload: dict, file: UploadFile):
        
        self.job_id = payload.get("job_id", "")
        self.metadata = payload.get("metadata", {})
        self.schema = payload.get("schema", {})

        self.payload = payload
        self.file = file

    def calc_cost_informations(self, model: str, schema: dict, scraper: str, result: dict):

        input = str(schema) + str(scraper)
        output = str(result)

        calculator = LLMCostCalculator(model=model)

        cost_informations = calculator.calculate(
            input_text=input,
            output_text=output
        )

        return cost_informations

    async def execute(self) -> dict:
        file_name, file_extension, file_bytes = await FileService.load(self.file)

        scraper = ContentExtractorService.extract(file_bytes, file_extension)
        scraper = scraper["response"]

        extractor = GenericTextExtractor(self.payload["schema"])
        parse = extractor.extract(scraper)

        #"""
        cost_informations = self.calc_cost_informations(
            model="gpt-4o-mini", 
            schema=self.schema,
            scraper=scraper,
            result=parse
        )
        #"""
        # cost_informations = "cost_informations"

        result = {
            "job_id": self.job_id,
            "len": len(scraper),
            "cost_informations": cost_informations,
            "parse": parse
        }

        return result


# python -m src.text_parse.text_parse_module