import os
from dotenv import load_dotenv
from typing import Any, List
from pydantic import BaseModel

from agno.tools import Toolkit

# Dataframe Analyzer Packages
import json
import pandas as pd

from io import BytesIO
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
        TOOL_RESPONSER (Any): Optional object responsible for collecting tool execution metadata.
    """
    def __init__(
        self,
        enable_dataframe_analyzer: bool = True,
        all: bool = False,
        TOOL_RESPONSER: Any = None,
        **kwargs,
    ):
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
            #"""
            with open("src/dataframe_analyzers/pd_df_agent/supermarket_sales.csv", "rb") as f:
                file_bytes = f.read()

            df = pd.read_csv(BytesIO(file_bytes))
            agent = DataframeAgent(
                dataframe=df,
            )

            report = agent.run_agent(query)
            print(json.dumps(report, indent=4))
            #"""

            md = """
### 📊 Análise do Gráfico de Barras: Quantidade de Pessoas por Gênero

O gráfico de barras apresenta a quantidade de pessoas por gênero. Nele, é possível observar a distribuição entre os gêneros representados na base de dados.

A barra correspondente a cada gênero indica a quantidade de indivíduos, permitindo uma comparação visual clara entre eles.

Esse tipo de visualização é útil para:
- entender a demografia da amostra  
- apoiar análises mais profundas  
- identificar possíveis diferenças de comportamento ou preferências entre grupos
"""

            #report = "Montre para o usuário o gráfico gerado: ![Graph_1](https://hsenyunovbrmjejxqvjn.supabase.co/storage/v1/object/public/images/image_generations/img_1771170203179075400QhZ3)"
            #print(md)

            # Collect metadata
            #self._update_response("dataframe_analyzer", {"md": md})
            self._update_response("dataframe_analyzer", {"report": report})

        except Exception as e:
            return f"Failed to generate context of research: {str(e)}"

        return report

if __name__ == "__main__":
    tool = DataframeAnalyzer()
    tool.dataframe_analyzer(
        #"Gere um grafico de barras da quantidade de pessoas por genero"
        "Qual a quantidade de pessoas por gênero"
    )

# python -m src.agents.sheet_analyzer.toolkit