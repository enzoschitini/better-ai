import pandas as pd
class Toolkit:
    def __init__(self):
        self.tool_result = []
    
    def _get_dataframe(self, dataframe):
        self.dataframe = dataframe
        return dataframe
    
    def _dataframe_preview(self, dataframe, format="text"):
        preview_df = dataframe.head(50)

        if format == "text":
            return preview_df.to_markdown(index=False)
        elif format == "dict":
            return preview_df.to_dict(orient="records")
        else:
            raise ValueError("Unsupported format. Use 'text' or 'dict'.")

    def _add_tool_result(self, tool_name, result, format="text"):
        if isinstance(result, pd.DataFrame):
            result = {
                "type": "dataframe",
                "preview": self._dataframe_preview(dataframe=result, format=format),
                "format": format,
                #"columns": list(result.columns),
                "shape": result.shape
            }

        self.tool_result.append({
            "tool_name": tool_name,
            "result": result
        })

    def _get_tools(self):
        return [
            {
                "name": "custom_calculation",
                "func": self.custom_calculation_tool,
                "description": "Performs a custom calculation based on the input string."
            },
            {
                "name": "knn",
                "func": self.knn,
                "description": "Performs KNN analysis based on the input string. For clustering or classification tasks."
            },
            {
                "name": "clean_data",
                "func": self.clean_data,
                "description": "Cleans the data based on the input string. For example, it can drop missing values or create new features."
            }
        ]

    def custom_calculation_tool(self, input: str) -> str:
        print(f"Running custom_calculation_tool with input: {input}")
        df = self.dataframe.head()
        print(f"DataFrame head:\n{df}")
        return f"Custom calculation result for: {input}. DataFrame head:\n{df}"
    
    def knn(self, input: str) -> str:
        print(f"Running knn tool with input: {input}")
        return f"KNN result for: {input}"
    
    def clean_data(self, input: str) -> str:
        print(f"Running clean_data tool with input: {input}")
        df = self.dataframe.head()
        df = df.dropna()
        df["cleaned"] = True
        self._add_tool_result("clean_data", df)

        return f"Cleaned data based on: {input}. DataFrame head:\n{df.to_markdown(index=False)}"








