import json

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

if __name__ == "__main__":
    response = {}
    formatter = FormatAgentResponse(response)
    super_json = formatter.serialize()

    print(json.dumps(super_json, indent=2))

