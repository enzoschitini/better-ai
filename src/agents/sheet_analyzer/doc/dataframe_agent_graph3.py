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

from src.agents.sheet_analyzer.doc.config import AgentConfig

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

        config = AgentConfig()
        self.id_model = config.id_model
        self.temperature = config.temperature
        self.agent_type = config.agent_type

        self.include_df_in_prompt = config.include_df_in_prompt
        self.number_of_head_rows = config.number_of_head_rows

        self.max_execution_time = config.max_execution_time
        self.early_stopping_method = config.early_stopping_method

        self.allow_dangerous_code = config.allow_dangerous_code
        self.verbose = config.verbose

        self.prefix = config.prefix
        self.suffix = config.suffix

        self.collector.patch_matplotlib()

    def _get_model(self):
        model = ChatOpenAI(model=self.id_model, temperature=self.temperature)
        self.model = model

        return model
    
    def create_agent(self):
        agent = create_pandas_dataframe_agent(
            llm=self.model,
            df=self.dataframe,
            agent_type=self.agent_type,

            prefix=self.prefix,
            suffix=self.suffix,

            include_df_in_prompt=self.include_df_in_prompt,
            number_of_head_rows=self.number_of_head_rows,

            max_execution_time=self.max_execution_time,
            early_stopping_method=self.early_stopping_method,

            allow_dangerous_code=self.allow_dangerous_code,
            verbose=self.verbose,
        )

        # 🔄 Reset collector
        self.collector.reset()

        self.agent = agent

        return agent
    
    def invoke(self):
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

        return final_response
    
    def run_agent(self):
        self._get_model()
        self.create_agent()
        respose = self.invoke()
        return respose







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
    respose = agent.run_agent()

    print(json.dumps(respose, indent=4))


# python -m src.agents.sheet_analyzer.doc.dataframe_agent_graph3