import yaml

class PromptLoader:
    def __init__(self, path: str):
        with open(path, "r", encoding="utf-8") as file:
            self.data = yaml.safe_load(file) or {}

    def get(self, key: str, **variables):
        value = self.data
        for k in key.split("."):
            value = value[k]

        return value.format(**variables) if isinstance(value, str) else value

