from io import BytesIO

import pandas as pd
from dotenv import load_dotenv

from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_experimental.agents import create_pandas_dataframe_agent

import json
from io import BytesIO
from langchain_community.callbacks import get_openai_callback

from src.agents.sheet_analyzer.doc.config import AgentConfig
from src.agents.sheet_analyzer.doc.plot_collector import PlotCollector
from src.agents.sheet_analyzer.doc.toolkit import Toolkit

load_dotenv()

class DataframeAgent:
    def __init__(self, dataframe, toolkit=None):
        config = AgentConfig()
        self.collector = PlotCollector()

        self.toolkit = toolkit
        self.dataframe = dataframe
        
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
    
    def _get_tools(self):
        extra_tools = []

        if self.toolkit is None:
            self.extra_tools = extra_tools
            return extra_tools
        
        self.toolkit._get_dataframe(self.dataframe)
        for tool in self.toolkit._get_tools():
            extra_tools.append(
                Tool(
                    name=tool["name"],
                    func=tool["func"],
                    description=tool["description"]
                )
            )

        self.extra_tools = extra_tools
        return extra_tools


    def create_agent(self):
        agent = create_pandas_dataframe_agent(
            llm=self.model,
            df=self.dataframe,
            agent_type=self.agent_type,
            extra_tools=self.extra_tools,

            prefix=self.prefix,
            suffix=self.suffix,

            include_df_in_prompt=self.include_df_in_prompt,
            number_of_head_rows=self.number_of_head_rows,

            max_execution_time=self.max_execution_time,
            early_stopping_method=self.early_stopping_method,

            allow_dangerous_code=self.allow_dangerous_code,
            verbose=self.verbose,
        )

        self.collector.reset()
        self.agent = agent

        return agent

    def invoke(self, user_query):
        with get_openai_callback() as cb:
            response = self.agent.invoke(user_query)

        final_response = {
            "input": response["input"],
            "graphs": self.collector.get_graphs(),
            "output": response["output"],
            "tool_result": self.toolkit.tool_result if self.toolkit else None,
            "usage": {
                "total_tokens": cb.total_tokens,
                "prompt_tokens": cb.prompt_tokens,
                "completion_tokens": cb.completion_tokens,
                "cost_usd": cb.total_cost,
            }
        }

        return final_response
    
    def run_agent(self, user_query: str = "Create a bar chart showing the number of passengers in each class."):
        self._get_model()
        self._get_tools()
        self.create_agent()
        return self.invoke(user_query)


if __name__ == "__main__":
    with open("src/agents/sheet_analyzer/doc/titanic.csv", "rb") as f:
        file_bytes = f.read()

    df = pd.read_csv(BytesIO(file_bytes))
    
    agent = DataframeAgent(
        dataframe=df,
        toolkit=Toolkit(),
    )
    respose = agent.run_agent(
        #"Use the custom_calculation tool to process 'example input'."
        #"Classify passengers into 'survived' and 'not survived"
        "Clean the data"
    )

    print(json.dumps(respose, indent=4))


# python -m src.agents.sheet_analyzer.doc.dataframe_agent_graph3