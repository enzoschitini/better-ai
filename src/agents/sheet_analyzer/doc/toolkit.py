
class Toolkit:
    def _get_dataframe(self, dataframe):
        self.dataframe = dataframe
        return dataframe
    
    def _get_tools(self):
        return [
            {
                "name": "custom_calculation",
                "func": self.custom_calculation_tool,
                "description": "Performs a custom calculation based on the input string."
            }
        ]

    def custom_calculation_tool(self, input: str) -> str:
        print(f"Running custom_calculation_tool with input: {input}")
        df = self.dataframe.head()
        print(f"DataFrame head:\n{df}")
        return f"Custom calculation result for: {input}. DataFrame head:\n{df}"








