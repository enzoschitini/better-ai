#from src.embedding.embedding_module
# python -m src.embedding.endpoint_api



from datetime import datetime, timezone

dt = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)
print(str(dt))

