import requests

#print(requests.get("http://localhost:7777/agents").json())

agent_id = "fair-goodall-9e694aa8"
agent_id = "laura94"

url = f"http://localhost:7777/agents/{agent_id}/runs"

data = {
    "message": "Explique o que é RAG",
    "session_id": "session-1",
    "stream": "false"
}

response = requests.post(url, data=data)
result = response.json()

#print(result)
print(f"\n\nResponse: {result["content"]}")

# http://localhost:7777/docs