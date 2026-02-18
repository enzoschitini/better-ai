import json
from src.database.no_sql.router import NoSQLRouter

manager = NoSQLRouter(backend="local")

"""
manager.save_payload("mydb", "users", {"name": "Enzo"})

docs = manager.fetch_documents("mydb", "users", {"name": "Enzo"})
print(json.dumps(docs, indent=4))

manager.update_documents("mydb", "users", {"name": "Enzo"}, {"age": 25})

manager.delete_documents("mydb", "users", {"name": "Enzo"})
"""

manager.save_payload("mydb", "users", {"name": "Enzo"})

# python -m src.database.no_sql.test