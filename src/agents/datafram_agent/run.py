import seaborn as sns
import pandas as pd

from src.utils.unique_id_factory import IDGenerator

from src.agents.datafram_agent.agent import DataframeAgent
from src.agents.agent_executor import AgentExecutor

dataframes = [
    {
        "id": "01",
        "name": "Titanic",
        "description": "Informações sobre os passageiros do Titanic.",
        "url": "https://github.com/mwaskom/seaborn-data/blob/master/titanic.csv",
        "loader": lambda: sns.load_dataset("titanic")
    },
    {
        "id": "02",
        "name": "Tips",
        "description": "Gorjetas em restaurante.",
        "url": "https://github.com/mwaskom/seaborn-data/blob/master/tips.csv",
        "loader": lambda: sns.load_dataset("tips")
    },
    {
        "id": "03",
        "name": "Penguins",
        "description": "Medidas físicas de pinguins (similar ao Iris).",
        "url": "https://github.com/mwaskom/seaborn-data/blob/master/penguins.csv",
        "loader": lambda: sns.load_dataset("penguins")
    },
    {
        "id": "04",
        "name": "Diamonds",
        "description": "Preço e atributos de diamantes.",
        "url": "https://github.com/mwaskom/seaborn-data/blob/master/diamonds.csv",
        "loader": lambda: sns.load_dataset("diamonds")
    },
    {
        "id": "05",
        "name": "Planets",
        "description": "Planetas descobertos por telescópios.",
        "url": "https://github.com/mwaskom/seaborn-data/blob/master/planets.csv",
        "loader": lambda: sns.load_dataset("planets")
    },
    {
        "id": "06",
        "name": "Flights",
        "description": "Passageiros de voo por mês.",
        "url": "https://github.com/mwaskom/seaborn-data/blob/master/flights.csv",
        "loader": lambda: sns.load_dataset("flights")
    },
    {
        "id": "07",
        "name": "Iris",
        "description": "Medidas de flores Iris (3 espécies).",
        "url": "https://github.com/mwaskom/seaborn-data/blob/master/iris.csv",
        "loader": lambda: pd.read_csv("https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv")
    },
]

def get_df(id: str) -> pd.DataFrame:
    entry = next((d for d in dataframes if d["id"] == id), None)
    if entry is None:
        raise ValueError(f"Dataset '{id}' não encontrado.")
    return entry["loader"]()


if __name__ == "__main__":
    import base64

    executor = AgentExecutor.from_agent_class(
        agent_class=DataframeAgent,
        params={
            "dataframe": get_df("01")
        },
        # session_id e user_id são opcionais — omita para usar os defaults
        # session_id=IDGenerator().uuid(),
        # user_id="user_01",
    )
    executor.run_cli_loop(print_tool_response=True)

    # Qual o numero de sobreviventes?
    # Gere um grafico de barra do numero de mortos e sobrevicentes 

# python -m src.agents.datafram_agent.run