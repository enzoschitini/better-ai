import json

class ManagerProcessInformations:
    def __init__(self, file_name: str = "process_output"):
        self.process_payload = {}
        self.file_name = file_name
    
    def add(self, key: str, value):
        self.process_payload[key] = value
    
    def remove(self, key: str):
        if key in self.process_payload:
            del self.process_payload[key]
    
    def get_payload(self):
        return self.process_payload
    
    def save(self):
        with open(f"{self.file_name}.json", "w") as f:
            json.dump(self.process_payload, f, indent=4, default=str)
