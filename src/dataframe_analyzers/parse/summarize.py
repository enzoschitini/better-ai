import json
import pandas as pd
from io import BytesIO

from src.dataframe_analyzers.pd_df_agent.agent import DataframeAgent
from src.vector_store.pinecone.test import TestPineconeVectorStore
from src.vector_store.pinecone.utils.retrieval_manager import RetrievalManager

from src.content_parse.content_parsing_agent import ContentParsingAgent

with open(f"src\\agents\\sheet_analyzer\\sheets\\OPEN_OTB_BACKTOOUTBACK.xlsx", "rb") as f:
    file_bytes = f.read()

df = pd.read_excel(BytesIO(file_bytes))

# Converte as primeiras linhas em markdown
markdown_table = df.head().to_markdown(index=False)
markdown_info = str(df.info())
print(markdown_table)
print(markdown_info)

def off():
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

def parse_content(input_data):
    output_data = {
        "table_summary": {
            "type": "str",
            "description": "A summary of the dataframe, including its main topics, themes, and insights",
        },

        "columns_summary": {
            "type": "list",
            "description": "A summary of each column in the dataframe",
            "items": {
                "type": "object",
                "description": "Summary of a column in the dataframe",
                "properties": {
                    "name": {
                        "type": "str",
                        "description": "Name of the column"
                    },
                    "summary": {
                        "type": "str",
                        "description": "A summary of the column"
                    },
                }
            }
        }
    }

    config_data = {
        "model_provider": "OpenAI",
        "model_id": "gpt-4.1-mini",
        "max_input_tokens": 1000000,
        "debug_mode": True,
        "instructions": "Extraia dados do texto",
        "description": "Leia o texto e extraia as informações relevantes conforme o esquema definido. Retorne um JSON estruturado com os dados extraídos. Caso não encontre alguma informação, retorne null para aquele campo."
    }

    agent_parser = ContentParsingAgent(
        input_data={
            "input_data": input_data,
        },
        output_data=output_data,
        config_data=config_data
    )

    content_parsed = agent_parser.run_agent()
    response = agent_parser.format_response(content_parsed)
    
    print(json.dumps(response, indent=4, ensure_ascii=False))

parse_content(markdown_table)


# python -m src.dataframe_analyzers.parse.summarize
