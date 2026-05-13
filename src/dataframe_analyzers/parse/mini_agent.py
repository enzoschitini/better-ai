import json
import pandas as pd
from io import BytesIO

from src.dataframe_analyzers.pd_df_agent.agent import DataframeAgent
from vector_store.pinecone.test.test import TestPineconeVectorStore
from src.vector_store.pinecone.utils.retrieval_manager import RetrievalManager

tester = TestPineconeVectorStore()
query = "Qual a média de idade de homens e mulheres que lembram de algum brinde do Outback?"
query = "Quais classes mais lembram das campanhas?"
query = "Qual tipo de ação promocional as mulheres preferem?"
query = "Quais os 5 principais pratos do outback que as pessoas mais sentem falta?"
query = "Quais os 5 principais pratos do outback que as pessoas mais sentem falta? (Desconsiderando as respostas 'Não' e 'Nenhum')"

documents = tester.retriver(
    query=query,
    filter_search={
        "file_id": [
            "ENQUETE_OTB_ACAOPROMO",
            "ENQUETE_OTB_BACKTOOUTBACK",
            "ESCALA_OTB_BACKTOOUTBACK",
            "MINISURVEY_OTB_BACKTOOUTBACK",
            "MINISURVEY_OTB_BRINDE",
            "OPEN_OTB_BACKTOOUTBACK"   
        ]
    },
    k=50
)

meneger = RetrievalManager(docs=documents)
context = meneger.generate_context()
files = meneger.get_files()
file_id = files[0]["id"]

with open("context.txt", "w", encoding="utf-8") as f:
    f.write(context)

print(f"Context: \n{context}\n")
print(f"File: \n{json.dumps(files[0], indent=2)}\n")
print(f"File ID: {file_id}\n")

def agent_analyze(query):
    with open(f"src\\agents\\sheet_analyzer\\sheets\\{file_id}.xlsx", "rb") as f:
        file_bytes = f.read()
  
    df = pd.read_excel(BytesIO(file_bytes))
    
    agent = DataframeAgent(dataframe=df)
    report = agent.run_agent(query)

agent_analyze(query)
print(f"File ID: {file_id}\n")

if __name__ == "__main__":
    pass

# python -m src.dataframe_analyzers.parse.mini_agent
