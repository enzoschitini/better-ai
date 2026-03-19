import requests
import json

def get_agents():
    response = requests.get("http://localhost:7777/agents").json()
    print(response)

    return response

class AgentRequest:
    def __init__(self, agent_id: str, host: str = "localhost:7777"):
        self.agent_id = agent_id
        self.host = host
        self.url = f"http://{host}/agents/{agent_id}/runs"
    
    def _get_connection(self, data: dict):
        self.response = requests.post(self.url, data=data, stream=True)

        return self.response

    def simple_request(self):
        result = self.response.json()

        #print(result)
        print(f"\n\nResponse: {result["content"]}")

    def simple_stream(self):
        for line in self.response.iter_lines():
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

    def stream_with_tools(self):
        for line in self.response.iter_lines():
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

    def show_all(self):
        for line in self.response.iter_lines():
            if line:
                decoded = line.decode("utf-8")
                print(decoded)

    def save(self):
        stream_response = []  # variável que vai guardar tudo

        with open("stream_output.txt", "w", encoding="utf-8") as file:

            for line in self.response.iter_lines():
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

if __name__ == "__main__":
    request = AgentRequest(agent_id="base-agent")
    request._get_connection(
        data={
            "message": "O que as pessoas tem dito sobre as olimpiadas de inverno?",
            "session_id": "session-1",
            "stream": "true"
        }
    )
    request.stream_with_tools()

    # Explique o que é RAG
    # http://localhost:7777/docs

# python -m src.agents.agent_flow.stream_agent