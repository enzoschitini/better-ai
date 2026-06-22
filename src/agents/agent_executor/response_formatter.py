import json
from pathlib import Path
from typing import Any, Dict


class ResponseFormatter:
    def __init__(self, response: Any):
        self.response = response

    def serialize(self, max_depth: int = 10) -> Any:
        def convert(value: Any, depth: int = 0) -> Any:
            if depth > max_depth:
                return str(value)

            if isinstance(value, (str, int, float, bool)) or value is None:
                return value

            if isinstance(value, (list, tuple, set)):
                return [convert(v, depth + 1) for v in value]

            if isinstance(value, dict):
                return {str(k): convert(v, depth + 1) for k, v in value.items()}

            if hasattr(value, "__dict__"):
                result: Dict[str, Any] = {}
                for key, item in vars(value).items():
                    if callable(item):
                        continue
                    try:
                        result[key] = convert(item, depth + 1)
                    except Exception:
                        result[key] = str(item)
                return result

            try:
                return str(value)
            except Exception:
                return None

        return convert(self.response)

    def clean_json(self, data: Any) -> Any:
        if isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                value = self.clean_json(value)
                if value in (None, 0, "", [], {}):
                    continue
                cleaned[key] = value
            return cleaned

        if isinstance(data, list):
            cleaned_list = [self.clean_json(value) for value in data]
            return [value for value in cleaned_list if value not in (None, 0, "", [], {})]

        return data

    def format(self) -> Dict[str, Any]:
        serialized = self.serialize()
        return self.clean_json(serialized)

    @staticmethod
    def save_json(data: Dict[str, Any], filepath: str) -> None:
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
