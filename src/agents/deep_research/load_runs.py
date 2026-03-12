import sqlite3
import json

conn = sqlite3.connect("src/agents/deep_research/agno.db")
cursor = conn.cursor()

cursor.execute("SELECT runs FROM agno_sessions")
rows = cursor.fetchall()

runs = []

for row in rows:
    raw = row[0]

    if raw:
        data = json.loads(raw)      # remove primeira camada
        data = json.loads(data)     # remove segunda camada
        runs.extend(data)           # junta na lista

with open("src/agents/deep_research/response.json", "w", encoding="utf-8") as f:
    json.dump(runs, f, indent=2, ensure_ascii=False)

print(json.dumps(runs, indent=2, ensure_ascii=False))