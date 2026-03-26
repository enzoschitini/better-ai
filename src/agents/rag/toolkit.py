from dotenv import load_dotenv
from typing import List, Dict, Any

from agno.tools import Toolkit

# Retriver Package
from src.vector_store.pinecone.pinecone_retriever import PineconeRetriever

load_dotenv()

class RetrievalManager:
    """
    Classe responsável por gerenciar documentos recuperados (retrieval),
    permitindo filtragem por score, geração de contexto compacto e extração de metadados de arquivos.

    :param docs: Lista de documentos contendo pelo menos 'text', 'score' e opcionalmente 'metadata'
    :param score_min: Valor mínimo de score para filtragem
    :param filter_by_score: Define se os documentos devem ser filtrados automaticamente na inicialização
    """
    def __init__(self, docs: List[Dict[str, Any]], score_min: float = 0.0, filter_by_score: bool = False):
        self.docs = docs
        self.score_min = score_min
        self.filter_by_score = filter_by_score

        if self.filter_by_score:
            self.docs = self.get_by_score(self.docs, self.score_min)

    def get_by_score(self, docs: List[Dict[str, Any]] = None, score_min: float = 0.0) -> List[Dict[str, Any]]:
        """
        Filtra itens de uma lista de documentos com base no score mínimo.

        :param docs: Lista de dicionários com a chave 'score'
        :param score_min: Valor mínimo de score (>=)
        :return: Lista filtrada
        """
        try:
            docs = docs or self.docs
            return [item for item in docs if item.get("score", 0) >= score_min]
        
        except Exception as e:
            raise RuntimeError("Failed to filter documents by score:", str(e))

    def generate_context(self, docs: List[Dict[str, Any]] = None) -> str:
        """
        Converte documentos para um formato compacto estilo toon.

        Cada linha segue o padrão:
        score|content

        :param docs: Lista de documentos (com 'text' e 'score')
        :return: String compacta para uso em LLM
        """
        try:
            docs = docs or self.docs

            return "\n".join(
                f"Score: {round(doc.get('score', 0), 2)} | Content: {doc.get('text', '').replace('\n', ' ')}"
                for doc in docs
            )

        except Exception as e:
            raise RuntimeError("Failed to generate context string:", str(e))

    def get_files(self, docs: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Extrai informações de arquivos a partir dos metadados dos documentos.

        Cada documento pode conter um campo 'metadata' com informações do arquivo original.
        Este método organiza esses dados em uma estrutura padronizada.

        :param docs: Lista de documentos contendo 'metadata'
        :return: Lista de dicionários com:
            - id: Identificador do arquivo
            - name: Nome do arquivo
            - ext: Extensão do arquivo
            - score: Score associado ao documento
        """
        try:
            docs = docs or self.docs
            files = []

            for doc in docs:
                metadata = doc.get("metadata", {})
                files.append({
                    "id": metadata.get("file_id", 0),
                    "name": metadata.get("file_name", 0),
                    "ext": metadata.get("file_extension", 0),
                    "score": doc.get("score", 0),
                })

            return files

        except Exception as e:
            raise RuntimeError("Failed to extract file metadata:", str(e))

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
        filter_search: dict,
        enable_get_relevant_documents: bool = True,
        all: bool = False,
        TOOL_RESPONSER: Any = None,
        **kwargs,
    ):
        self.filter_search = filter_search
        self.TOOL_RESPONSER = TOOL_RESPONSER
        tools: List[Any] = []

        if all or enable_get_relevant_documents:
            tools.append(self.get_relevant_documents)

        super().__init__(name="get_relevant_documents_tools", tools=tools, **kwargs)
    
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
            retriver = PineconeRetriever()

            documents = retriver.similarity_search(
                query=query,
                k=5,
                filter_search=self.filter_search
            )

            manager = RetrievalManager(docs=documents)
            context = manager.generate_context()

            # Collect metadata
            self._update_response(
                "get_relevant_documents", 
                {"files": manager.get_files()}
            )

        except Exception as e:
            return f"Failed to generate context of research: {str(e)}"

        return context

if __name__ == "__main__":
    import json

    tool = RetrievalAugmentedGeneration(
        filter_search={
            "file_id": ["candidatura", "tenerezza", "cucinare"]
        }
        #{"collection_id": "collection_01"}
    )
    result = tool.get_relevant_documents("Enzo Schitini")

    print(f"\n\n{result}\n")


# python -m src.agents.rag.toolkit