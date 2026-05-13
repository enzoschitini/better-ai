import json
from src.embedding.applications import DeleteEmbeddings

deleter = DeleteEmbeddings()
result = deleter.delete(
    target_keys=["source"],
    target_values=["uploaded_file"]
)

print(json.dumps(result, indent=4))
# python -m src.embedding.test.delete