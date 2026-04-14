import os
from dotenv import load_dotenv

from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_community.callbacks import get_openai_callback

from src.dataframe_analyzers.pd_df_agent.config import AgentConfig
from src.dataframe_analyzers.pd_df_agent.plot_collector import PlotCollector
from src.tracing.tracing_core import ApplicationTracing

load_dotenv()

tracer = ApplicationTracing(
    flag="DataframeAgent",
    file_name="agent.py",
    log_file_name="dataframe_agent"
)

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

        tracer.INFO(
            message=f"DataframeAgent initialized with configuration", 
            metadata={
                "id_model": self.id_model,
                "model_provider": self.model_provider,
                "temperature": self.temperature,
                "agent_type": self.agent_type,
                "include_df_in_prompt": self.include_df_in_prompt,
                "number_of_head_rows": self.number_of_head_rows,
                "max_execution_time": self.max_execution_time,
                "early_stopping_method": self.early_stopping_method,
                "allow_dangerous_code": self.allow_dangerous_code,
                "verbose": self.verbose,
                "prefix": self.prefix,
                "suffix": self.suffix,
            }
        )

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
            tracer.INFO(message=f"Model initialized: {provider} - {self.id_model}")
            return model

        except Exception as e:
            tracer.ERROR(
                func_name="_get_model",
                message=f"Error initializing model: {str(e)}"
            )
            raise RuntimeError(f"Error initializing model: {str(e)}")
    
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
            tracer.INFO(message=f"Tools initialized: {[tool.name for tool in extra_tools]}")
            return extra_tools
        
        except Exception as e:
            tracer.ERROR(
                func_name="_get_tools",
                message=f"Error initializing tools: {str(e)}"
            )
            raise RuntimeError(f"Error initializing tools: {str(e)}")

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
            tracer.INFO(message=f"Agent created successfully")

            return agent
        
        except Exception as e:
            tracer.ERROR(
                func_name="create_agent",
                message=f"Error creating agent: {str(e)}"
            )
            raise RuntimeError(f"Error creating agent: {str(e)}")

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

            tracer.INFO(
                message=f"""
\n\n############################## AGENT INVOCATION ##############################\n\n
Agent invoked. User query: '{user_query}'.

Response: 
{response['output']}

Graphs generated: {len(self.collector.get_graphs())}
\n\n##############################################################################\n\n
"""
            )
            return final_response
        
        except Exception as e:
            tracer.ERROR(
                func_name="invoke",
                message=f"Error invoking agent: {str(e)}"
            )
            raise RuntimeError(f"Error invoking agent: {str(e)}")
    
    def run_agent(self, user_query: str = "Create a bar chart showing the number of passengers in each class."):
        self._get_model()
        self._get_tools()
        self.create_agent()
        return self.invoke(user_query)

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




if __name__ == "__main__":
    import pandas as pd
    from io import BytesIO

    with open("src\\agents\\sheet_analyzer\\sheets\\ENQUETE_OTB_ACAOPROMO.xlsx", "rb") as f:
        file_bytes = f.read()
    
    use_chat = True
    df = pd.read_excel(BytesIO(file_bytes))
    
    toolkit = BasicDataframeToolkit()
    agent = DataframeAgent(dataframe=df, toolkit=toolkit)

    if use_chat:
        print("\n\nDigite sua pergunta (ou 'cls' para encerrar):")
        
        while True:
            ask = input("\n>>> ")
            
            if ask.lower() in ["cls", "sair", "exit", "quit"]:
                print("Encerrando...")
                break
            
            try:
                report = agent.run_agent(ask)
            except Exception as e:
                print(f"Erro: {e}")
    else:
        report = agent.run_agent(
            #"Gere um grafico de barras da quantidade de pessoas por genero"
            #"Qual a quantidade de pessoas por gênero"
            "Quais generos foram representados na pesquisa?"
        )

# Monte uma tabela relacionado resposta e classe. Com o percentual de resposta de cada classe para cada resposta
# Crie uma tabela da média de idade por resposta
# Qual a média de idade por resposta?
# Quais as 5 principais respostas da pesquisa?
# Qual a média de idade por classe?
# Divida as idades em 3 grupos e diga a quantidade de respostas por grupo
# python -m src.dataframe_analyzers.pd_df_agent.agent