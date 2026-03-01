import json
from src.database.no_sql.router import DocumentStore

manager = DocumentStore(backend="local")

"""
manager.save_payload("mydb", "users", {"name": "Enzo"})

docs = manager.fetch_documents("mydb", "users", {"name": "Enzo"})
print(json.dumps(docs, indent=4))

manager.update_documents("mydb", "users", {"name": "Enzo"}, {"age": 25})

manager.delete_documents("mydb", "users", {"name": "Enzo"})
"""

response = manager.save_payload("mydb", "users", {"name": "Enzo"})
print(response["inserted_id"])
# python -m src.database.no_sql.test