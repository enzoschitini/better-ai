import json
from src.tracing.tracing_core import ApplicationTracing

tracer = ApplicationTracing(
    log_id="001",
    flag="Test Debug",
    log_file_name="debug"
)

class ClasseUno:
    def __init__(self, text: str):
        self.text = text
    
    def get_text(self, value: int):
        try:
            r = 6 / 0
            response = f"Il testo era: {self.text}.{value}"
        except Exception as e:
            
            raise RuntimeError("ClasseUno Error", str(e))

        return response

class Run:
    def __init__(self, text: str):
        self.uno = ClasseUno(text)
    
    def run(self, value: int):
        try:
            # r = 6 / 0
            response = self.uno.get_text(5)
        except Exception as e:
            
            raise RuntimeError("Run Error", str(e))

        return response

runner = Run("testo")
response = runner.run(5)

print(response)

# python -m local.debug