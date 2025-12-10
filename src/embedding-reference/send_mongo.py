from src.knowledge_base.database.mongo_database_client import MongoDatabaseClient
from src.knowledge_base.database.mongo_execution_manager import MongoExecutionManager

from src.knowledge_base.cost_calculator.cost_calculator import CostCalculator
from src.knowledge_base.cost_calculator.exchange_rate_manager import ExchangeRateManager
from src.knowledge_base.cost_calculator.config import PRICING_MODELS

db_client = MongoDatabaseClient()
exchange_rate_manager = ExchangeRateManager(database_client=db_client)

calculator = CostCalculator(
    pricing_models=PRICING_MODELS, exchange_rate_manager=exchange_rate_manager
)

def calc_cost(processing_info):
    file_extension = processing_info["file_extension"]

    image_extensions = {"jpg", "jpeg", "png", "webp", "gif"}
    audio_extensions = {"mp3", "wav", "flac", "aac", "m4a", "wma"}

    if file_extension.lower() in image_extensions:
        #Imagem

        result = calculator.calculate_cost_output(
                file_extension=file_extension,
                modelo_extracao="gemini-1.5-pro",
                modelo_embedding="text-embedding-ada-002",
                prompt=processing_info["prompt"],
                output_gerado=processing_info["output_gerado"], 
                input_tokens=processing_info["input_tokens"],
                output_tokens=processing_info["output_tokens"]
            )
    
    elif file_extension.lower() in audio_extensions:
        #Áudio

        result = calculator.calculate_cost_output(
                file_extension=file_extension,
                modelo_extracao="gemini-1.5-pro",
                modelo_embedding="text-embedding-ada-002",
                prompt=processing_info["prompt"],
                output_gerado=processing_info["output_gerado"], 
                input_tokens=processing_info["input_tokens"],
                output_tokens=processing_info["output_tokens"]
            )
    
    else:
        #Doc

        result = calculator.calculate_cost_output(
            file_extension=file_extension,
            modelo_embedding="text-embedding-ada-002",
            output_gerado=processing_info["output_gerado"],
        )
    
    return result


def save_process(payload):
    processing_info = calc_cost(payload["processing_info"])

    mongo = MongoExecutionManager()

    execution_id = mongo.insert_execution(
        job_id=payload["job_id"],
        metadata=payload["metadata"],
        processing_info=processing_info,
        file_info=payload["file_info"],
        status="SUCCEEDED",
        start_time=payload["start_time"],
        end_time=payload["end_time"]
    )

    return execution_id
 