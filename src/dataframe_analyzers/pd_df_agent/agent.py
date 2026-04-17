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
    """
    This class encapsulates the creation and invocation of an agent that interacts with dataframes using language models.
    It configures the agent based on detailed parameters and integrates custom tools for data manipulation.

    Args:
    :param dataframe (pd.DataFrame): The dataframe on which the agent will operate.
    :param toolkit (BasicDataframeToolkit, optional): A set of additional tools for dataframe manipulation. Default is None.
    :param id_model (str, optional): Identifier of the language model. Default is defined by AgentConfig.
    :param model_provider (str, optional): Model provider, such as "openai". Default is defined by AgentConfig.
    :param temperature (float, optional): Degree of randomness in the model responses. Default is defined by AgentConfig.
    :param agent_type (str, optional): Type of agent to be created. Default is defined by AgentConfig.
    :param include_df_in_prompt (bool, optional): Whether the dataframe will be included in the prompt. Default is defined by AgentConfig.
    :param number_of_head_rows (int, optional): Number of initial rows of the dataframe to consider. Default is defined by AgentConfig.
    :param max_execution_time (int, optional): Maximum execution time allowed for the agent. Default is defined by AgentConfig.
    :param early_stopping_method (str, optional): Early stopping method for the agent. Default is defined by AgentConfig.
    :param allow_dangerous_code (bool, optional): Allows execution of potentially dangerous code. Default is defined by AgentConfig.
    :param verbose (bool, optional): Whether operations will be displayed in detail. Default is defined by AgentConfig.
    :param prefix (str, optional): Prefix text for the agent prompt. Default is defined by AgentConfig.
    :param suffix (str, optional): Suffix text for the agent prompt. Default is defined by AgentConfig.

    Methods:
            create_agent(): Creates and configures the pandas dataframe agent based on the class properties and settings.
            invoke(user_query): Invokes the agent with a user query and returns the formatted response.
            run_agent(user_query): Executes the full flow of initializing and invoking the agent with a query.
    """
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
        """
        Initializes and returns the language model according to the specified provider.
        If not specified, the default provider from the configuration is used.

        Args:
        provider (str, optional): Name of the model provider. Default is None.

        Returns:
                model: Instance of the configured language model.

        Raises:
                ValueError: If the provided provider is not in the list of valid providers.
                RuntimeError: If an error occurs during model initialization.
        """
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
        """
        Generates and returns the list of extra tools based on the provided toolkit.
        If no toolkit is configured, returns an empty list.

        Returns:
                list: List of tools configured for the agent.

        Raises:
                RuntimeError: If an error occurs during tool initialization.
        """
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
        """
        Creates and configures the pandas dataframe agent using the model, tools, and parameters specified in the class.

        Returns:
                agent: Instance of the created agent ready for interaction.

        Raises:
                RuntimeError: If an error occurs during agent creation.
        """
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
        """
        Sends a query to the agent and retrieves the response along with token usage information.

        Args:
        user_query (str): Textual query sent to the agent.

        Returns:
                dict: Dictionary containing the user input, agent response, tool output (if any), and usage metrics.

        Raises:
                RuntimeError: If an error occurs during agent invocation.
        """
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

            tracer.INFO(message=f"Agent invoked successfully", metadata={"response": final_response})
            return final_response
        
        except Exception as e:
            tracer.ERROR(
                func_name="invoke",
                message=f"Error invoking agent: {str(e)}"
            )
            raise RuntimeError(f"Error invoking agent: {str(e)}")
    
    def run_agent(
            self, 
            user_query: str = "Create a bar chart showing the number of passengers in each class."
        ):
        """
        Executes the full flow to initialize the model, load tools, create the agent, and invoke the user query.

        Args:
        user_query (str, optional): Query for the agent. Default is "Create a bar chart showing the number of passengers in each class.".

        Returns:
                dict: Formatted response from the agent after executing the query.
        """
        self._get_model()
        self._get_tools()
        self.create_agent()
        return self.invoke(user_query)
