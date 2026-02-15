from src.database.mongo_manager import MongoDBManager
from src.image_generation.utils.config import (
    BUCKET_NAME, STORAGE_BASE_PATH, DATABASE_NAME, COLLECTION_NAME
)
from src.storage.storage_repository import StorageRepository

def save_process(mongo_payload, images):
    try:
        mongo = MongoDBManager()

        result = mongo.save_payload(
            database_name=DATABASE_NAME,
            collection_name=COLLECTION_NAME,
            payload=mongo_payload
        )
    except Exception as e:
        raise RuntimeError("Erro ao salvar no mongo")

    try:
        repository = StorageRepository(
            base_path=STORAGE_BASE_PATH,
            bucket_name=BUCKET_NAME
        )

        for image in images:
            repository.upload_to_supabase(
                file_name=image["id"],
                byte_data=image["byte"]
            )

    except Exception as e:
        raise RuntimeError("Erro ao salvar no no storage")

"""
dic = {
    "test": "TEST_CLASS"
}

mongo = MongoDBManager()
result = mongo.save_payload(
    database_name="DB_TEST_CLASS",
    collection_name="COL_TEST_CLASS",
    payload=dic
)

print(result)


for image in images:
    repository = StorageRepository(
        base_path=STORAGE_BASE_PATH,
        bucket_name=BUCKET_NAME
    )

    repository.upload_to_supabase(
        file_name=image["id"],
        byte_data=image["byte"]
    )
"""

storage_payload = [
    {
        "id": "img-177099605352876790040BY",
        "url": "https://example.com/generated_image_img-177099605352876790040BY.png",
        "mime_type": "image/png",
        "byte": "xxxxxxxxxxxxxxx"
    },
    {
        "id": "img-1770996053528767900Uhl7",
        "url": "https://example.com/generated_image_img-1770996053528767900Uhl7.png",
        "mime_type": "image/png",
        "byte": "xxxxxxxxxxxxxxx"
    }
]





# SaveProcess: mongo_payload, images

# python -m src.image_generation.save_mongo
