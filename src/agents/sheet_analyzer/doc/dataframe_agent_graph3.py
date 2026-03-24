import os
import uuid
import base64
from io import BytesIO

import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv

from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_experimental.agents import create_pandas_dataframe_agent

import json
from io import BytesIO
from langchain_community.callbacks import get_openai_callback

load_dotenv()

class PlotCollector:
    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = output_dir
        self.graphs = []

        os.makedirs(self.output_dir, exist_ok=True)

    def custom_show(self):
        buffer = BytesIO()
        filename = f"{self.output_dir}/plot_{uuid.uuid4().hex}.png"

        plt.savefig(filename)
        plt.savefig(buffer, format="png")
        plt.close()

        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode("utf-8")

        graph_data = {
            "file_path": filename,
            "image_base64": img_base64[:100]  # preview
        }

        self.graphs.append(graph_data)

        return graph_data

    def patch_matplotlib(self):
        plt.show = self.custom_show  # 🔥 monkey patch

    def reset(self):
        self.graphs = []

    def get_graphs(self):
        return self.graphs

class DataframeAgent:
    def __init__(self, 
                dataframe,):
        
        self.dataframe = dataframe
        self.collector = PlotCollector()
        self.collector.patch_matplotlib()
        self.model = self._get_model()
        self.agent = self.create_agent()

    def _get_model(self):
        model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
        )

        return model
    
    def create_agent(self):
        agent = create_pandas_dataframe_agent(
            llm=self.model,
            df=self.dataframe,
            agent_type="tool-calling",

            prefix="""
    You are a data analyst working with a pandas DataFrame called `df`.

    Rules:
    - ALWAYS use the provided dataframe `df`
    - NEVER load external datasets

    When creating plots:
    - ALWAYS use matplotlib
    - ALWAYS call plt.show() at the end
    """,

            suffix="""
    Provide the final answer clearly.

    IMPORTANT:
    - Do NOT include any image links, file paths, or markdown images
    - Do NOT mention where the chart is saved
    - Assume the chart is already displayed in the interface
    - Only describe the insights from the chart
    """,

            include_df_in_prompt=True,
            number_of_head_rows=5,

            max_execution_time=10,
            early_stopping_method="force",

            allow_dangerous_code=True,
            verbose=True,
        )

        # 🔄 Reset collector
        self.collector.reset()

        return agent
    
    def run_agent(self):
        with get_openai_callback() as cb:
            response = self.agent.invoke(
                "Create a bar chart showing the number of passengers in each class.",
            )
            
        # 📦 Resultado final
        final_response = {
            "input": response["input"],
            "graphs": self.collector.get_graphs(),
            "output": response["output"],
            "usage": {
                "total_tokens": cb.total_tokens,
                "prompt_tokens": cb.prompt_tokens,
                "completion_tokens": cb.completion_tokens,
                "cost_usd": cb.total_cost,
            }
        }

        print(json.dumps(final_response, indent=4))

        return final_response





# =========================
# 🚀 Main
# =========================
if __name__ == "__main__":
    # =========================
    # 📊 Simulando bytes (ex: vindo do banco)
    # =========================
    with open("src/agents/sheet_analyzer/doc/titanic.csv", "rb") as f:
        csv_bytes = f.read()

    # 🔥 carregar via bytes
    df = pd.read_csv(BytesIO(csv_bytes))
    
    agent = DataframeAgent(dataframe=df)
    agent.run_agent()
