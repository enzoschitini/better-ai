import os
from dotenv import load_dotenv
from typing import Any, List
from pydantic import BaseModel

from agno.tools import Toolkit

# Dataframe Analyzer Packages
import json
import pandas as pd

from src.vector_store.pinecone.pinecone_retriever import PineconeRetriever

load_dotenv()

class RetrievalAugmentedGeneration(Toolkit):
    """
    Toolkit for structured data analysis using DataFrames.

    This toolkit provides tools to:
    - explore tabular datasets
    - generate statistical summaries
    - identify patterns and insights
    - produce analytical reports

    Args:
        enable_dataframe_analyzer (bool): Enables the dataframe analysis tool. Defaults to True.
        all (bool): Enables all available tools. Overrides individual flags when True. Defaults to False.
        TOOL_RESPONSER (Any): Optional object responsible for collecting tool execution metadata.
    """
    def __init__(
        self,
        enable_dataframe_analyzer: bool = True,
        all: bool = False,
        TOOL_RESPONSER: Any = None,
        **kwargs,
    ):
        self.TOOL_RESPONSER = TOOL_RESPONSER
        tools: List[Any] = []

        if all or enable_dataframe_analyzer:
            tools.append(self.dataframe_analyzer)

        super().__init__(name="dataframe_analyzer_tools", tools=tools, **kwargs)
    
    def _update_response(self, tool_name: str, payload: dict):
        """
        Internal helper method used to collect metadata about tool execution.
        """
        if self.TOOL_RESPONSER:
            self.TOOL_RESPONSER.add_metadata(
                tool_name=tool_name,
                payload=payload
            )

    def get_relevant_documents(self, query: str) -> str:
        """
        dataframe_analyzer is a tool for runs an automated analysis on a DataFrame and returns a structured report based on a user-provided query.

        ⚠️ IMPORTANT:
        - The dataset is ALREADY loaded internally.
        - The user DOES NOT need to provide any file or data.
        - NEVER ask the user for the dataset.
        - ALWAYS execute the analysis using the available internal data.

        The tool is responsible for:
        - interpreting the query
        - analyzing the internal dataframe
        - generating insights and visualizations (if applicable)

        Args:
            query (str): User query or instruction related to the dataset
                         (e.g., "analyze sales by region", "find revenue patterns").

        Returns:
            str: A report containing analysis results, insights, and possible visualizations. IN MARKDOWN
        """
        try:
            #"""
            #"""
            response = "xxx"

            # Collect metadata
            self._update_response("dataframe_analyzer", {"md": "md"})

        except Exception as e:
            return f"Failed to generate context of research: {str(e)}"

        return response

if __name__ == "__main__":
    import json

    """
    retriver = PineconeRetriever()
    results = retriver.similarity_search(
        query="MESCOLARE ",
        k=5,
        filter_search={
            "file_id": "cucinare"
        }
    )

    print(json.dumps(results, indent=4))
    """


base = {
    "id": "79258322-c06b-4e50-9a69-c8caa1136b3f",
    "text": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "metadata": {
        "Client": "1234",
        "client_id": "0011",
        "collection_id": "collection_01",
        "collection_name": "BetterAI",
        "created_at": "2026-03-25 18:58:43",
        "file_extension": "pdf",
        "file_id": "cucinare",
        "file_name": "LESSICO per CUCINARE.pdf",
        "user_id": "11"
    },
    "score": 0.382682741
}

lista = [
    {
        "id": "79258322-c06b-4e50-9a69-c8caa1136b3f",
        "text": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "metadata": {
            "Client": "1234",
            "client_id": "0011",
            "collection_id": "collection_01",
            "collection_name": "BetterAI",
            "created_at": "2026-03-25 18:58:43",
            "file_extension": "pdf",
            "file_id": "cucinare",
            "file_name": "LESSICO per CUCINARE.pdf",
            "user_id": "11"
        },
        "score": 0.382682741
    },

    {
        "id": "f75b0f7c-36ab-48d4-8da0-ec21b9ce688a",
        "text": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "metadata": {
            "Client": "1234",
            "client_id": "0011",
            "collection_id": "collection_01",
            "collection_name": "BetterAI",
            "created_at": "2026-03-25 18:58:43",
            "file_extension": "pdf",
            "file_id": "cucinare",
            "file_name": "LESSICO per CUCINARE.pdf",
            "user_id": "11"
        },
        "score": 0.359430343
    }
]

from typing import List, Dict, Any

# 1. Filter relevant documents by score

def filter_by_score(documents: List[Dict[str, Any]], score_min: float = 0.0) -> List[Dict[str, Any]]:
    """
    Filtra itens de uma lista de documentos com base no score mínimo.

    :param documents: Lista de dicionários com a chave 'score'
    :param score_min: Valor mínimo de score (>=)
    :return: Lista filtrada
    """
    return [item for item in documents if item.get("score", 0) >= score_min]

#print(json.dumps(filter_by_score(documents=lista), indent=4))

def generate_context(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Converte uma lista de documentos no formato padrão de contexto.

    :param documents: Lista de documentos (com 'text' e 'score')
    :return: Lista de dicionários com 'score' e 'content'
    """
    context = []

    for doc in documents:
        context.append({
            "score": round(doc.get("score", 0), 2),
            "content": doc.get("text", "")
        })

    return str(context)

def generate_context(documents: List[Dict[str, Any]]) -> str:
    """
    Converte documentos para um formato compacto estilo toon.

    Cada linha segue o padrão:
    score|content

    :param documents: Lista de documentos (com 'text' e 'score')
    :return: String compacta para uso em LLM
    """
    return "\n".join(
        f"Score: {round(doc.get('score', 0), 2)} | Content: {doc.get('text', '').replace('\n', ' ')}"
        for doc in documents
    )

print(generate_context(documents=lista))

def get_files(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    files = []

    for doc in documents:
        metadata = doc.get("metadata", {})
        files.append({
            "id": metadata.get("file_id", 0),
            "name": metadata.get("file_name", 0),
            "ext": metadata.get("file_extension", 0),
            "score": doc.get("score", 0),
        })

    return files

#print(json.dumps(get_files(documents=lista), indent=4))

# python -m src.agents.rag.toolkit