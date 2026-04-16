import json
import pandas as pd
from io import BytesIO

from src.dataframe_analyzers.pd_df_agent.agent import DataframeAgent
from src.vector_store.pinecone.test import TestPineconeVectorStore
from src.vector_store.pinecone.utils.retrieval_manager import RetrievalManager

with open(f"src\\agents\\sheet_analyzer\\sheets\\OPEN_OTB_BACKTOOUTBACK.xlsx", "rb") as f:
    file_bytes = f.read()

df = pd.read_excel(BytesIO(file_bytes))
print(df.head())

tester = TestPineconeVectorStore()
query = "Sobre o que aborda a tabela?"

documents = tester.retriver(
    query=query,
    filter_search={
        "file_id": [
            "ENQUETE_OTB_ACAOPROMO",
            #"ENQUETE_OTB_BACKTOOUTBACK",
            #"ESCALA_OTB_BACKTOOUTBACK",
            #"MINISURVEY_OTB_BACKTOOUTBACK",
            #"MINISURVEY_OTB_BRINDE",
            #"OPEN_OTB_BACKTOOUTBACK"   
        ]
    },
    k=50
)

meneger = RetrievalManager(docs=documents)
context = meneger.generate_context()

print(f"Context: \n{context}\n")

if __name__ == "__main__":
    pass

# python -m src.dataframe_analyzers.parse.summarize
