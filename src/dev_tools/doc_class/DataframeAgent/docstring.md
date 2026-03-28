```python
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
    Classe para criar um agente que interage com DataFrames usando modelos de linguagem e ferramentas auxiliares. 
    Permite configurar o modelo, ferramentas, agentes e executar consultas que geram respostas e visualizações baseadas nos dados.

    Args: 
        dataframe (DataFrame): O DataFrame pandas que será analisado pelo agente.
        toolkit (object, optional): Conjunto de ferramentas para manipulação do DataFrame. Default é None.
        id_model (str, optional): Identificador do modelo a ser utilizado. Default é None.
        model_provider (str, optional): Provedor do modelo (ex: 'openai', 'gemini'). Default é None.
        temperature (float, optional): Parâmetro de temperatura para geração do modelo. Default é None.
        agent_type (str, optional): Tipo do agente para criação. Default é None.
        include_df_in_prompt (bool, optional): Se deve incluir parte do DataFrame no prompt. Default é None.
        number_of_head_rows (int, optional): Número de linhas do DataFrame a incluir no prompt. Default é None.
        max_execution_time (int, optional): Tempo máximo de execução do agente. Default é None.
        early_stopping_method (str, optional): Método de parada antecipada. Default é None.
        allow_dangerous_code (bool, optional): Permite que o código perigoso seja executado. Default é None.
        verbose (bool, optional): Nível de verbosidade do agente. Default é None.
        prefix (str, optional): Texto de prefixo para o prompt do agente. Default é None.
        suffix (str, optional): Texto de sufixo para o prompt do agente. Default é None.

    Methods:
            run_agent(user_query): Executa o agente com uma consulta do usuário e retorna a resposta e visualizações geradas.
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
        Inicializa o modelo de linguagem apropriado baseado no provedor especificado ou na configuração padrão.

        Args: 
            provider (str, optional): Nome do provedor do modelo (ex: 'openai', 'gemini'). Default é None (usa configuração do agente).

        Returns:
            model: Instância do modelo inicializado para utilização pelo agente.
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
        Cria e inicializa a lista de ferramentas baseadas no toolkit associado ao DataFrame para o agente utilizar.

        Returns:
            list[Tool]: Lista de ferramentas encapsuladas no formato Tool para uso pelo agente.
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
        Cria o agente pandas DataFrame configurado com o modelo, ferramentas e parâmetros definidos.

        Returns:
            agent: Instância do agente criada e pronta para receber consultas.
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
        Invoca o agente com a consulta do usuário e coleta a resposta, gráficos e uso de tokens.

        Args:
            user_query (str): Consulta do usuário para o agente processar.

        Returns:
            dict: Dicionário contendo a entrada, saída, gráficos gerados, resultado de ferramentas e estatísticas de uso de tokens.
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

            tracer.INFO(message=f"Agent invoked. User query: '{user_query}'. Response: '{response['output']}'")
            return final_response
        
        except Exception as e:
            tracer.ERROR(
                func_name="invoke",
                message=f"Error invoking agent: {str(e)}"
            )
            raise RuntimeError(f"Error invoking agent: {str(e)}")
    
    def run_agent(self, user_query: str = "Create a bar chart showing the number of passengers in each class."):
        """
        Executa o fluxo completo do agente: inicializa o modelo, ferramentas, cria o agente e processa a consulta do usuário.

        Args:
            user_query (str): Consulta do usuário para o agente processar. Default é uma instrução para criar um gráfico de barras.

        Returns:
            dict: Resposta consolidada do agente contendo resultados, gráficos e informações da execução.
        """
        self._get_model()
        self._get_tools()
        self.create_agent()
        return self.invoke(user_query)
```