import os
from typing import List, Optional, Dict, Any, Union

from src.vector_store.pinecone.pinecone_client import PineconeClient
from src.vector_store.config import PineconeVectorStoreConfig
from src.tracing.tracing_core import ApplicationTracing


tracer = ApplicationTracing(
    flag="PineconeRetriever",
    file_name="pinecone_retriever.py",
    log_file_name="pinecone_module"
)


def trace(method_name: str):
    """
    Decorator para padronizar logging e captura de erros.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer.INFO(method_name, "Execution started")
            try:
                result = func(*args, **kwargs)
                tracer.INFO(method_name, "Execution finished successfully")
                return result
            except Exception as e:
                tracer.ERROR(method_name, "Execution failed", error=e)
                raise
        return wrapper
    return decorator


class PineconeRetriever:
    """
    Serviço responsável por realizar operações de recuperação
    (retrieval) de vetores no Pinecone.

    Esta classe atua como uma camada de acesso ao índice vetorial,
    encapsulando:
    - Buscas por similaridade
    - Recuperação de vetores por metadados
    - Interação direta com o índice Pinecone

    Seu objetivo é oferecer uma API clara e segura para leitura
    de dados vetoriais.
    """

    def __init__(self, client: Optional[PineconeClient] = None):
        """
        Inicializa o PineconeRetriever a partir de um PineconeClient.

        Responsabilidades:
        - Validar a dependência principal (PineconeClient)
        - Extrair e armazenar os componentes necessários para consulta:
            - índice
            - mecanismo de embeddings
            - namespace padrão

        Parâmetros:
        - client (PineconeClient): 
            Objeto previamente configurado contendo:
            - index: referência ao índice Pinecone
            - embeddings: provedor de embeddings
            - namespace: namespace padrão para consultas

        Exceções:
        - ValueError: se o client não for fornecido
        """
        tracer.INFO("__init__", "Initializing retriever")

        try:
            # ==========================
            # Validação / Injeção
            # ==========================
            if not client:
                tracer.DEBUG("__init__", "No client provided, creating default client")
                client = PineconeClient()

            # ==========================
            # Configurações
            # ==========================
            self.config = PineconeVectorStoreConfig()
            self.batch_size = self.config.embedding_batch_size
            self.dimension = self.config.dimensions

            # ==========================
            # Dependências
            # ==========================
            self.index = client.index
            self.embeddings = client.embedding_model
            self.namespace = client.main_namespace

            tracer.DEBUG(
                "__init__",
                "Retriever initialized",
                metadata={
                    "batch_size": self.batch_size,
                    "dimension": self.dimension,
                    "namespace": self.namespace,
                }
            )

        except Exception as e:
            tracer.ERROR("__init__", "Failed to initialize retriever", error=e)
            raise

    # ======================================================
    # Similarity Search
    # ======================================================

    @trace("similarity_search")
    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter_search: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executa uma busca por similaridade vetorial no índice Pinecone.

        Responsabilidades:
        - Validar os parâmetros de entrada (query e k)
        - Gerar o embedding da consulta textual
        - Construir filtros compatíveis com o Pinecone ($eq ou $in)
        - Executar a consulta vetorial no índice
        - Normalizar a resposta para o formato interno da aplicação

        Parâmetros:
        - query (str): Texto usado como base para a busca por similaridade.
        - k (int): Quantidade máxima de resultados a serem retornados.
        - filter_search (Optional[Dict[str, Any]]): 
            Filtro opcional no formato {campo: valor} ou {campo: [valores]}.
            Exemplo:
                {"file_id": "abc123"}
                {"file_id": ["a", "b", "c"]}

        Retorno:
        - List[Dict[str, Any]]: Lista de documentos similares contendo:
            - id: identificador do vetor
            - text: conteúdo textual (se existir no metadata)
            - metadata: metadados associados ao vetor
            - score: score de similaridade retornado pelo Pinecone
        """
        # ==========================
        # Validações
        # ==========================
        if not query:
            tracer.ERROR("similarity_search", "Empty query received")
            raise ValueError("The search query cannot be empty.")

        if k <= 0:
            tracer.ERROR("similarity_search", "Invalid k value", metadata={"k": k})
            raise ValueError("The parameter k must be greater than zero.")

        # ==========================
        # Embedding
        # ==========================
        try:
            tracer.DEBUG(
                "similarity_search",
                "Generating embedding",
                metadata={"query_preview": query[:50]}
            )

            query_vector = self.embeddings.embed_query(query)

        except Exception as e:
            tracer.ERROR(
                "similarity_search",
                "Failed to generate embedding",
                error=e
            )
            raise RuntimeError("Failed to generate query embedding.") from e

        # ==========================
        # Filtro
        # ==========================
        filter_query: Optional[Dict[str, Any]] = None

        try:
            if filter_search:
                key, value = list(filter_search.items())[0]

                if isinstance(value, list):
                    filter_query = {key: {"$in": value}}
                else:
                    filter_query = {key: {"$eq": value}}

                tracer.DEBUG(
                    "similarity_search",
                    "Filter applied",
                    metadata={"filter": filter_query}
                )

        except Exception as e:
            tracer.ERROR(
                "similarity_search",
                "Invalid filter",
                metadata={"filter_search": filter_search},
                error=e
            )
            raise ValueError("Invalid search filter.") from e

        # ==========================
        # Query Pinecone
        # ==========================
        try:
            tracer.DEBUG(
                "similarity_search",
                "Querying Pinecone",
                metadata={"k": k, "namespace": self.namespace}
            )

            results = self.index.query(
                vector=query_vector,
                top_k=k,
                namespace=self.namespace,
                include_metadata=True,
                filter=filter_query,
            )

        except Exception as e:
            tracer.ERROR(
                "similarity_search",
                "Pinecone query failed",
                error=e
            )
            raise RuntimeError("Failure to query Pinecone.") from e

        # ==========================
        # Normalização
        # ==========================
        documents: List[Dict[str, Any]] = []

        try:
            for match in getattr(results, "matches", []):
                metadata = match.get("metadata", {}).copy()

                document = {
                    "id": match.get("id"),
                    "text": metadata.get("text", ""),
                    "metadata": metadata,
                    "score": match.get("score"),
                }

                document["metadata"].pop("text", None)
                documents.append(document)

            tracer.DEBUG(
                "similarity_search",
                "Results processed",
                metadata={"results_count": len(documents)}
            )

        except Exception as e:
            tracer.ERROR(
                "similarity_search",
                "Failed to process results",
                error=e
            )
            raise RuntimeError("Failed to process search results.") from e

        return documents

    # ======================================================
    # Metadata Search
    # ======================================================

    @trace("get_all_docs_by_metadata")
    def get_all_docs_by_metadata(
        self,
        batch_size: int | None = None,
        dimension: int | None = None,
        target_key: str = "file_id",
        target_value: Union[str, List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Recupera vetores do Pinecone com base em um filtro direto por metadata.

        Esta função NÃO realiza busca semântica. Ela utiliza um vetor "dummy"
        apenas para satisfazer o contrato da API do Pinecone, enquanto a
        recuperação real é feita exclusivamente via filtro por metadata
        (target_key / target_value).

        É possível buscar por um único valor ou por uma lista de valores,
        utilizando automaticamente os operadores `$eq` ou `$in`.

        O método faz paginação explícita para garantir a recuperação de
        TODOS os vetores associados ao filtro informado.

        Responsabilidades:
        - Montar dinamicamente o filtro de metadata
        - Executar queries paginadas no Pinecone
        - Normalizar o retorno para o formato interno da aplicação

        Limitações conhecidas:
        - A API do Pinecone exige a presença de um vetor na query
        - A ordem dos resultados não é garantida
        - O campo `score` não possui significado semântico neste contexto

        :param batch_size: Quantidade máxima de vetores retornados por requisição.
                        Controla paginação, uso de memória e latência.
        :param dimension: Dimensão do vetor do índice (necessária para o dummy vector).
        :param target_key: Chave do metadata usada como filtro (ex: file_id, user_id).
        :param target_value: Valor ou lista de valores usados no filtro.
        :return: Lista de vetores recuperados do Pinecone.
        """
        if not target_value:
            tracer.ERROR(
                "get_all_docs_by_metadata",
                "target_value is empty"
            )
            raise ValueError("target_value cannot be empty.")

        batch_size = (
            min(batch_size, self.batch_size)
            if batch_size and batch_size > 0
            else self.batch_size
        )

        dimension = (
            dimension if dimension and dimension > 0 else self.dimension
        )

        dummy_vector = [0.0] * dimension

        # Filtro dinâmico
        if isinstance(target_value, list):
            filter_query = {target_key: {"$in": target_value}}
        else:
            filter_query = {target_key: {"$eq": target_value}}

        tracer.DEBUG(
            "get_all_docs_by_metadata",
            "Starting paginated retrieval",
            metadata={
                "target_key": target_key,
                "batch_size": batch_size,
                "namespace": self.namespace,
            }
        )

        results: List[Dict[str, Any]] = []
        pagination_token: Optional[str] = None

        try:
            while True:
                response = self.index.query(
                    vector=dummy_vector,
                    namespace=self.namespace,
                    top_k=batch_size,
                    include_metadata=True,
                    include_values=False,
                    filter=filter_query,
                    pagination_token=pagination_token,
                )

                for match in response.get("matches", []):
                    results.append(
                        {
                            "id": match["id"],
                            "metadata": match.get("metadata", {}),
                            "score": match.get("score"),
                        }
                    )

                pagination_token = (
                    response.get("pagination", {}) or {}
                ).get("next")

                if not pagination_token:
                    break

            tracer.DEBUG(
                "get_all_docs_by_metadata",
                "Retrieval completed",
                metadata={"total_results": len(results)}
            )

        except Exception as e:
            tracer.ERROR(
                "get_all_docs_by_metadata",
                "Failed during paginated retrieval",
                metadata={
                    "target_key": target_key,
                    "target_value": target_value,
                },
                error=e
            )
            raise RuntimeError(
                "Failed to retrieve vectors by target."
            ) from e

        return results