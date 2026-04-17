import json
import pandas as pd

from io import BytesIO
from src.dataframe_analyzers.pd_df_agent.agent import DataframeAgent
from src.dataframe_analyzers.pd_df_agent.toolkit import BasicDataframeToolkit


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
            print(
                f"""
\n\n############################## AGENT INVOCATION ##############################\n\n
Agent invoked. User query: '{ask}'.

Response: 
{report['output']}

Graphs generated: {report['graphs']}
\n\n##############################################################################
"""
        )
        except Exception as e:
            print(f"Erro: {e}")
else:
    report = agent.run_agent(
        #"xxxxxxxxxx"
    )

# python -m src.dataframe_analyzers.pd_df_agent.test