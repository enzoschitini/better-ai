import pandas as pd
from typing import Any, List

from agno.tools import Toolkit

# Dataframe Analyzer Packages
from src.dataframe_analyzers.pd_df_agent.agent import DataframeAgent

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
        TOOL_RESPONSER (Any): Optional object responsible for collecting tool execution metadata.
    """
    def __init__(
        self,
        dataframe: pd.DataFrame,
        enable_dataframe_analyzer: bool = True,
        all: bool = False,
        TOOL_RESPONSER: Any = None,
        **kwargs,
    ):
        self.dataframe = dataframe
        self.TOOL_RESPONSER = TOOL_RESPONSER
        tools: List[Any] = []

        if all or enable_dataframe_analyzer:
            tools.append(self.dataframe_analyzer)

        super().__init__(name="dataframe_analyzer_tools", tools=tools, **kwargs)
    
    def _update_response(self, tool_name: str, payload: dict):
        """
        Internal helper method used to collect metadata about tool execution.
        """
        if self.TOOL_RESPONSER:
            self.TOOL_RESPONSER.add_metadata(
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
    import seaborn as sns
    import pandas as pd
    #from sklearn.datasets import load_iris

    # ── Datasets do Seaborn ──────────────────────────────────────────
    # Todos os datasets: https://github.com/mwaskom/seaborn-data
    # https://github.com/mwaskom/seaborn-data/blob/master/titanic.csv
    # https://github.com/mwaskom/seaborn-data/blob/master/tips.csv
    # https://github.com/mwaskom/seaborn-data/blob/master/penguins.csv
    # https://github.com/mwaskom/seaborn-data/blob/master/diamonds.csv
    # https://github.com/mwaskom/seaborn-data/blob/master/planets.csv
    # https://github.com/mwaskom/seaborn-data/blob/master/flights.csv

    df = sns.load_dataset("titanic")       # Titanic
    # df = sns.load_dataset("tips")        # Gorjetas em restaurante
    # df = sns.load_dataset("penguins")    # Pinguins (similar ao Iris)
    # df = sns.load_dataset("diamonds")    # Diamantes
    # df = sns.load_dataset("planets")     # Planetas
    # df = sns.load_dataset("flights")     # Passageiros de voo por mês
    # df = sns.load_dataset("fmri")        # Dados de neuroimagem

    # ── Iris via sklearn ─────────────────────────────────────────────
    # iris = load_iris(as_frame=True)
    # df = iris.frame   # inclui a coluna 'target' com o número da classe
    # df["species"] = iris.target_names[df["target"]]  # nome legível

    # ── Datasets nativos do pandas ───────────────────────────────────
    # (pandas não tem datasets próprios, mas você pode puxar direto da web)
    # df = pd.read_csv("https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv")

    tool = DataframeAnalyzer(dataframe=df)
    response = tool.dataframe_analyzer("Qual o numero de sobreviventes?")
    print(response)

# python -m src.agents.datafram_agent.tools.toolkit