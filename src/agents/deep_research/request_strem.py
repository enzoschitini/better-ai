import requests
import json

agent_id = "laura94"
url = f"http://localhost:7777/agents/{agent_id}/runs"

data = {
    "message": "Explique o que é RAG",
    "session_id": "session-1",
    "stream": "true"
}

response = requests.post(url, data=data, stream=True)

for line in response.iter_lines():
    if line:
        decoded = line.decode("utf-8")
        print(decoded)