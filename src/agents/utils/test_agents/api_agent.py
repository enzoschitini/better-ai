import json

from src.agents.agent_executor import AgentApiClient

PORT = "8000" # 7777 8000


class AgentRequest:
    def __init__(self, agent_id: str, host: str = f"localhost:{PORT}"):
        self.agent_id = agent_id
        self.host = host
        host_parts = host.split(":")
        host_name = host_parts[0]
        host_port = int(host_parts[1]) if len(host_parts) > 1 else 7777
        self.client = AgentApiClient(agent_id=agent_id, host=host_name, port=host_port)
        self.response = None
    
    def get_connection(self, data: dict):
        stream = str(data.get("stream", "false")).lower() == "true"
        if stream:
            self.response = self.client.run_stream(
                message=data.get("message", ""),
                session_id=data.get("session_id"),
                user_id=data.get("user_id"),
                extra_payload={},
            )
        else:
            self.response = self.client.run_direct(
                message=data.get("message", ""),
                session_id=data.get("session_id"),
                user_id=data.get("user_id"),
                extra_payload={},
            )
        return self.response

    def simple_request(self):
        result = self.response or {}

        print(f"\n\nResponse: {result.get('content', '')}")

    def simple_stream(self):
        for event in self.response or []:
            if event.get("event") == "RunContent":
                print(event.get("content", ""), end="", flush=True)

    def stream_with_tools(self):
        for event in self.response or []:
            event_type = event.get("event")

            if event_type == "RunContent":
                print(event.get("content", ""), end="", flush=True)
            elif event_type == "ToolCallStarted":
                print(f"\nTOOL STARTED: {event.get('tool', {}).get('tool_name')}")
            elif event_type == "ToolCallCompleted":
                print(f"\nTOOL COMPLETED: {event.get('tool', {}).get('tool_name')}")

    def show_all(self):
        for event in self.response or []:
            print(json.dumps(event, ensure_ascii=False))

    def save(self):
        stream_response = []  # variável que vai guardar tudo

        with open("stream_output.txt", "w", encoding="utf-8") as file:

            for event in self.response or []:
                decoded = json.dumps(event, ensure_ascii=False)

                # salva na variável
                stream_response.append(decoded)

                # salva no arquivo
                file.write(decoded + "\n")

                # opcional: mostrar no terminal
                print(decoded)
        
        print("\nStream salvo com sucesso!")

if __name__ == "__main__":
    request = AgentRequest(agent_id="rag_agent")
    request.get_connection(
        data={
            "message": "Quais arquivos estão na base?",
            "session_id": "session-1234567",
            "stream": "true",
        }
    )
    request.stream_with_tools()

    # Explique o que é RAG
    # http://localhost:7777/docs


# python -m src.agents.utils.test_agents.api_agent