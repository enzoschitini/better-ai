import os
import json
import pandas as pd

from io import BytesIO
from dotenv import load_dotenv

from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_community.callbacks import get_openai_callback

from src.dataframe_analyzers.pd_df_agent.config import AgentConfig
from src.dataframe_analyzers.pd_df_agent.plot_collector import PlotCollector
from src.dataframe_analyzers.pd_df_agent.toolkit import Toolkit

load_dotenv()

class DataframeAgent:
    def __init__(
        self,
        dataframe,
        toolkit=None,
        id_model=None,
        model_provider=None,
        temperature=None,
        agent_type=None,
        include_df_in_prompt=None,
        number_of_head_rows=None,
        max_execution_time=None,
        early_stopping_method=None,
        allow_dangerous_code=None,
        verbose=None,
        prefix=None,
        suffix=None,
    ):
        config = AgentConfig()
        self.collector = PlotCollector()

        self.dataframe = dataframe
        self.toolkit = toolkit

        # Fallback seguro
        self.id_model = id_model if id_model is not None else config.id_model
        self.model_provider = model_provider if model_provider is not None else config.model_provider
        self.temperature = temperature if temperature is not None else config.temperature
        self.agent_type = agent_type if agent_type is not None else config.agent_type
        self.valid_providers = config.valid_providers

        self.include_df_in_prompt = (
            include_df_in_prompt
            if include_df_in_prompt is not None
            else config.include_df_in_prompt
        )

        self.number_of_head_rows = (
            number_of_head_rows
            if number_of_head_rows is not None
            else config.number_of_head_rows
        )

        self.max_execution_time = (
            max_execution_time
            if max_execution_time is not None
            else config.max_execution_time
        )

        self.early_stopping_method = (
            early_stopping_method
            if early_stopping_method is not None
            else config.early_stopping_method
        )

        self.allow_dangerous_code = (
            allow_dangerous_code
            if allow_dangerous_code is not None
            else config.allow_dangerous_code
        )

        self.verbose = verbose if verbose is not None else config.verbose

        self.prefix = prefix if prefix is not None else config.prefix
        self.suffix = suffix if suffix is not None else config.suffix

        self.collector.patch_matplotlib()

    def _get_model(self, provider: str = None):
        try:
            VALID_PROVIDERS = self.valid_providers
            provider = (provider or self.model_provider).strip().lower()

            if provider not in VALID_PROVIDERS:
                raise ValueError(
                    f"Invalid provider '{provider}'. Valid options: {VALID_PROVIDERS}"
                )

            if provider == "openai":
                model = ChatOpenAI(
                    model=self.id_model, 
                    temperature=self.temperature
                )
            elif provider == "gemini":
                model = ChatGoogleGenerativeAI(
                    model=self.id_model,
                    google_api_key=os.getenv("GEMINI_API_KEY"),
                    temperature=self.temperature
                )

            self.model = model
            return model

        except Exception as e:
            raise ValueError(f"Error initializing model: {str(e)}")
    
    def _get_tools(self):
        try:
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
        
        except Exception as e:
            raise ValueError(f"Error initializing tools: {str(e)}")

    def create_agent(self):
        try:
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
        
        except Exception as e:
            raise ValueError(f"Error creating agent: {str(e)}")

    def invoke(self, user_query):
        try:
            with get_openai_callback() as cb:
                response = self.agent.invoke(user_query)

            final_response = {
                "input": response["input"],
                "output": response["output"],
                "graphs": self.collector.get_graphs(),
                "tool_result": self.toolkit.tool_result if self.toolkit else None,
                "usage": {
                    "input_tokens": cb.prompt_tokens,
                    "output_tokens": cb.completion_tokens,
                    "total_tokens": cb.total_tokens,
                    "cost_usd": cb.total_cost,
                }
            }

            return final_response
        
        except Exception as e:
            raise ValueError(f"Error invoking agent: {str(e)}")
    
    def run_agent(self, user_query: str = "Create a bar chart showing the number of passengers in each class."):
        self._get_model()
        self._get_tools()
        self.create_agent()
        return self.invoke(user_query)


if __name__ == "__main__":
    with open("src/dataframe_analyzers/pd_df_agent/supermarket_sales.csv", "rb") as f:
        file_bytes = f.read()

    df = pd.read_csv(BytesIO(file_bytes))
    agent = DataframeAgent(
        dataframe=df,
        #toolkit=Toolkit(),
    )

    respose = agent.run_agent(
        #"Use the custom_calculation tool to process 'example input'."
        #"Classify passengers into 'survived' and 'not survived"
        #"Clean the data"
        #"Quero um grafico de barra com a media de idade por sexo"
        #"Qual o nome do passageiro mais velho que sobreviveu?"
        #"Gere um grafico de pizza com a percentual de crianças, adultos e idosos"
        #"Gere um grafico de barras com a média de cada resposta na primeira pergunta"
        #"Gere um grafico de barras com a quantidade de respostas ao longo dos meses"
        #"Gere um grafico de barras com a quantidade de respostas por estado"
        #"Gere um grafico nuvem de palavras da quantidade de respostas por estado"
        "Gere um grafico de barras da quantidade de pessoas por genero"
        #"Oi"

    )

    print(json.dumps(respose, indent=4))

    # 1. Analisar mais de uma tabela de uma planilha

# python -m src.dataframe_analyzers.pd_df_agent.agent