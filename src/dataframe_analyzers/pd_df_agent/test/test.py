import json
import os
import base64
import pandas as pd

from io import BytesIO
from src.dataframe_analyzers.pd_df_agent.agent import DataframeAgent
from src.dataframe_analyzers.pd_df_agent.toolkit import BasicDataframeToolkit


with open("src/dataframe_analyzers/pd_df_agent/test/supermarket_sales.csv", "rb") as f:
    file_bytes = f.read()

if file_bytes.startswith(b"\x50\x4B\x03\x04"):  # Verificar se é um arquivo Excel (ZIP)
    df = pd.read_excel(BytesIO(file_bytes))

elif file_bytes.startswith(b"\xFF\xFE") or file_bytes.startswith(b"\xFE\xFF") or file_bytes.startswith(b"\xEF\xBB\xBF") or b"," in file_bytes[:1000]:  # Verificar se é um arquivo CSV
    df = pd.read_csv(BytesIO(file_bytes))

use_chat = True

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
            output = report['output']

            graphs_dict = report['graphs']

            output_dir = "outputs"
            os.makedirs(output_dir, exist_ok=True)

            graphs_file_path = []

            for graph in graphs_dict:
                file_name = graph["file_name"]
                file_path = os.path.join(output_dir, file_name)

                # Decodifica e salva imagem
                image_bytes = base64.b64decode(graph["image_base64"])
                with open(file_path, "wb") as f:
                    f.write(image_bytes)

                graphs_file_path.append({
                    "file_path": file_path
                })

            graphs_output = "\n".join(
                f"- {graph['file_path']}" for graph in graphs_file_path
            )

            print(
                f"""
\n\n############################## AGENT INVOCATION ##############################\n\n
User query: '{ask}'.

Response: 
{output}

Graphs generated:
{graphs_output}
\n\n##############################################################################
"""
        )
        except Exception as e:
            print(f"Erro: {e}")
else:
    report = agent.run_agent(
        #"Gere um grafico de barra da quantidade de homens e mulheres"
    )

# python -m src.dataframe_analyzers.pd_df_agent.test.test