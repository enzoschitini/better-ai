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
        data = json.loads(raw)  # converte string JSON -> dict
        runs.append(data)

#print(runs)
data = json.loads(runs)

with open("src/agents/deep_research/response.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(json.dumps(data, indent=2, ensure_ascii=False))

