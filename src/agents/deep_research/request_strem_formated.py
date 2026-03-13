import requests
import json

agent_id = "laura94"
url = f"http://localhost:7777/agents/{agent_id}/runs"

data = {
    "message": "O que as pessoas tem dito sobre as olimpiadas de inverno?",
    "session_id": "session-1",
    "stream": "true"
}

response = requests.post(url, data=data, stream=True)

def simple():
    for line in response.iter_lines():
        if not line:
            continue

        decoded = line.decode("utf-8")

        if decoded.startswith("data:"):
            json_str = decoded.replace("data:", "").strip()

            try:
                event = json.loads(json_str)

                if event.get("event") == "RunContent":
                    print(event.get("content", ""), end="", flush=True)

            except:
                pass

def with_tools():
    for line in response.iter_lines():
        if not line:
            continue

        decoded = line.decode("utf-8")

        if decoded.startswith("data:"):
            json_str = decoded.replace("data:", "").strip()

            try:
                event = json.loads(json_str)

                event_type = event.get("event")

                # texto do agente
                if event_type == "RunContent":
                    print(event.get("content", ""), end="", flush=True)

                # tool começou
                elif event_type == "ToolCallStarted":
                    print(f"\n🔧 TOOL CHAMADA: {event.get('tool_name')}")

                # tool terminou
                elif event_type == "ToolCallCompleted":
                    print(f"\n✅ TOOL FINALIZADA: {event.get('tool_name')}")

            except:
                pass

def save():
    stream_response = []  # variável que vai guardar tudo

    with open("stream_output.txt", "w", encoding="utf-8") as file:

        for line in response.iter_lines():
            if not line:
                continue

            decoded = line.decode("utf-8")

            # salva na variável
            stream_response.append(decoded)

            # salva no arquivo
            file.write(decoded + "\n")

            # opcional: mostrar no terminal
            print(decoded)
    
    print("\nStream salvo com sucesso!")

save()

# Explique o que é RAG