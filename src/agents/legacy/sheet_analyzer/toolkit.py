import os
import json
import pandas as pd

from dotenv import load_dotenv
from typing import Any, List

from agno.tools import Toolkit

# Dataframe Analyzer Packages
from src.dataframe_analyzers.pd_df_agent.agent import DataframeAgent

load_dotenv()

class DataframeAnalyzer(Toolkit):
    """
    Toolkit for structured data analysis using DataFrames.

    This toolkit provides tools to:
    - explore tabular datasets
    - generate statistical summaries
    - identify patterns and insights
    - produce analytical reports

    Args:
        enable_dataframe_analyzer (bool): Enables the dataframe analysis tool. Defaults to True.
        all (bool): Enables all available tools. Overrides individual flags when True. Defaults to False.
        tool_context (Any): Optional object responsible for collecting tool execution metadata.
    """
    def __init__(
        self,
        dataframe: pd.DataFrame,
        enable_dataframe_analyzer: bool = True,
        all: bool = False,
        tool_context: Any = None,
        **kwargs,
    ):
        self.dataframe = dataframe
        self.tool_context = tool_context
        tools: List[Any] = []

        if all or enable_dataframe_analyzer:
            tools.append(self.dataframe_analyzer)

        super().__init__(name="dataframe_analyzer_tools", tools=tools, **kwargs)
    
    def _update_response(self, tool_name: str, payload: dict):
        """
        Internal helper method used to collect metadata about tool execution.
        """
        if self.tool_context:
            self.tool_context.add_metadata(
                tool_name=tool_name,
                payload=payload
            )

    def dataframe_analyzer(self, query: str) -> str:
        """
        dataframe_analyzer is a tool for runs an automated analysis on a DataFrame and returns a structured report based on a user-provided query.

        ⚠️ IMPORTANT:
        - The dataset is ALREADY loaded internally.
        - The user DOES NOT need to provide any file or data.
        - NEVER ask the user for the dataset.
        - ALWAYS execute the analysis using the available internal data.

        The tool is responsible for:
        - interpreting the query
        - analyzing the internal dataframe
        - generating insights and visualizations (if applicable)

        Args:
            query (str): User query or instruction related to the dataset
                         (e.g., "analyze sales by region", "find revenue patterns").

        Returns:
            str: A report containing analysis results, insights, and possible visualizations. IN MARKDOWN
        """
        try:
            agent = DataframeAgent(
                dataframe=self.dataframe,
            )

            report = agent.run_agent(query)
            response = report["output"]

            self._update_response("dataframe_analyzer", {"response": response})

        except Exception as e:
            return f"Failed to generate context of research: {str(e)}"

        return response


if __name__ == "__main__":
    from io import BytesIO

    with open("src/dataframe_analyzers/pd_df_agent/test/supermarket_sales.csv", "rb") as f:
        file_bytes = f.read()

    df = pd.read_csv(BytesIO(file_bytes))

    tool = DataframeAnalyzer(dataframe=df)
    tool.dataframe_analyzer(
        "Qual a média de preço?"
    )

# python -m src.agents.sheet_analyzer.toolkit