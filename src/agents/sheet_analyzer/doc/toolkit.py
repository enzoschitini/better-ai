
class Toolkit:
    def __init__(self):
        pass

    def custom_calculation_tool(self, input: str) -> str:
        return f"Custom calculation result for: {input}"
    
    def _get_tools(self):
        return [
            {
                "name": "custom_calculation",
                "func": self.custom_calculation_tool,
                "description": "Performs a custom calculation based on the input string."
            }
        ]









