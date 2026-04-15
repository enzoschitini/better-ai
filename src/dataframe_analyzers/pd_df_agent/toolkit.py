import io

class BasicDataframeToolkit:
    def __init__(self):
        self.df = None
        self.tool_result = None

    def _get_dataframe(self, df):
        self.df = df

    def _get_tools(self):
        return [
            {
                "name": "get_dataframe_head",
                "func": self.get_head,
                "description": (
                    "Use this tool whenever you need to inspect, explore, or understand the structure "
                    "and content of the dataframe. This includes requests such as previewing the data, "
                    "seeing sample rows, checking column values, understanding the dataset layout, "
                    "or getting a quick overview of the data. "
                    "It returns the first 5 rows of the dataframe as a readable table."
                )
            },

            {
                "name": "get_dataframe_structure",
                "func": self.get_dataframe_structure,
                "description": (
                    "Use this tool to understand the structure of the dataframe, including column names, "
                    "data types, and non-null counts. This is especially useful when you need to know what "
                    "columns are available, their data types, or if there are any missing values. It provides "
                    "a summary of the dataframe's structure, which can help in deciding how to analyze or manipulate the data."
                )
            }
        ]

    def get_head(self, _=None):
        result = self.df.head(5).to_string()
        self.tool_result = result
        return result
    
    def get_dataframe_structure(self, _=None):
        buffer = io.StringIO()
        self.df.info(buf=buffer)
        result = buffer.getvalue()
        
        markdown_result = f"```\n{result}\n```"
        self.tool_result = markdown_result
        return markdown_result
