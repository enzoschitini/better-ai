import json
import pandas as pd

from io import BytesIO
from src.dataframe_analyzers.pd_df_agent.agent import DataframeAgent
from src.dataframe_analyzers.pd_df_agent.toolkit import Toolkit

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