import json
from pathlib import Path

class FormatAgentResponse:
    def __init__(self, response: str):
        self.response = response

    def serialize(self, max_depth=10):

        def convert(value, depth=0):
            if depth > max_depth:
                return str(value)

            # tipos primitivos
            if isinstance(value, (str, int, float, bool)) or value is None:
                return value

            # listas e tuplas
            if isinstance(value, (list, tuple, set)):
                return [convert(v, depth + 1) for v in value]

            # dicionários
            if isinstance(value, dict):
                return {
                    str(k): convert(v, depth + 1)
                    for k, v in value.items()
                }

            # objetos python
            if hasattr(value, "__dict__"):
                result = {}
                for k, v in vars(value).items():
                    if callable(v):
                        continue
                    try:
                        result[k] = convert(v, depth + 1)
                    except Exception:
                        result[k] = str(v)
                return result

            # fallback
            try:
                return str(value)
            except Exception:
                return None

        return convert(self.response)

    def clean_json(self, data):

        if isinstance(data, dict):
            cleaned = {}
            for k, v in data.items():
                v = self.clean_json(v)

                if v in (None, 0, "", [], {}):
                    continue

                cleaned[k] = v

            return cleaned

        elif isinstance(data, list):
            cleaned_list = [self.clean_json(v) for v in data]
            return [v for v in cleaned_list if v not in (None, 0, "", [], {})]

        else:
            return data

    def save_json(self, data: dict, filepath: str):
        path = Path(filepath)

        # cria a pasta caso não exista
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def format(self):
        """Serializa e limpa automaticamente"""
        serialized = self.serialize()
        return self.clean_json(serialized)

if __name__ == "__main__":
    class RunMetrics:
        def __init__(self):
            self.input_tokens = 45
            self.output_tokens = 1098
            self.total_tokens = 1143
            self.latency = 1.42
            self.cached_tokens = 0


    class ToolCall:
        def __init__(self):
            self.name = "search_web"
            self.arguments = {
                "query": "latest AI news",
                "language": "en",
                "limit": 5
            }
            self.result = [
                {"title": "OpenAI releases new model", "url": "https://example.com"},
                {"title": "AI regulation debate", "url": "https://example2.com"},
                {}
            ]


    class AgentResponse:
        def __init__(self):
            self.id = "run_847294"
            self.agent = "news-writer-agent"

            self.message = {
                "role": "assistant",
                "content": "Here are the latest AI news."
            }

            self.tools_used = [
                ToolCall()
            ]

            self.metrics = RunMetrics()

            self.metadata = {
                "session_id": "sess_111",
                "user_id": "user_22",
                "debug": None
            }

            self.extra = {
                "empty_string": "",
                "empty_list": [],
                "empty_dict": {},
                "zero_value": 0
            }

    response = AgentResponse()
    formatter = FormatAgentResponse(response)
    super_json = formatter.format()
    formatter.save_json(super_json, "src/agents/agent_flow/agent_response.json")

    print(json.dumps(super_json, indent=2))

# python -m src.agents.agent_flow.format_response
