import logging
from typing import List, Optional, Dict, Any, Union

from src.vector_store.pinecone_client import PineconeClient

logger = logging.getLogger(__name__)

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

    def __init__(self, client: PineconeClient):
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

        # ==========================
        # Validação de dependência
        # ==========================

        if not client:
            logger.error("PineconeClient cannot be None.")
            raise ValueError("PineconeClient cannot be None.")

        # ==========================
        # Injeção de dependências
        # ==========================

        # Índice Pinecone utilizado nas consultas
        self.index = client.index

        # Serviço responsável por gerar embeddings
        self.embeddings = client.embeddings

        # Namespace padrão para isolamento lógico dos vetores
        self.namespace = client.namespace



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
        # Validação de parâmetros
        # ==========================

        # Evita chamadas desnecessárias ao Pinecone
        if not query:
            logger.error("The search query cannot be empty.")
            raise ValueError("The search query cannot be empty.")

        if k <= 0:
            logger.error("The parameter k must be greater than zero.")
            raise ValueError("The parameter k must be greater than zero.")

        # ==========================
        # Geração do embedding
        # ==========================

        try:
            # Converte o texto da query em um vetor numérico
            query_vector = self.embeddings.embed_query(query)

        except Exception as e:
            logger.exception("Failed to generate query embedding.")
            raise RuntimeError("Failed to generate query embedding.") from e

        # ==========================
        # Construção do filtro
        # ==========================

        filter_query: Optional[Dict[str, Any]] = None

        try:
            # Suporte a filtros simples ($eq) ou listas ($in)
            # Exemplo final esperado pelo Pinecone:
            # {"file_id": {"$eq": "123"}}
            # {"file_id": {"$in": ["a", "b"]}}
            if filter_search:
                key, value = list(filter_search.items())[0]

                if isinstance(value, list):
                    filter_query = {key: {"$in": value}}
                else:
                    filter_query = {key: {"$eq": value}}

        except Exception as e:
            logger.exception("Invalid search filter: %r", filter_search)
            raise ValueError("Invalid search filter.") from e

        # ==========================
        # Consulta ao Pinecone
        # ==========================

        try:
            results = self.index.query(
                vector=query_vector,
                top_k=k,
                namespace=self.namespace,
                include_metadata=True,
                filter=filter_query,
            )

        except Exception as e:
            logger.exception("Failure to query Pinecone.")
            raise RuntimeError("Failure to query Pinecone.") from e

        # ==========================
        # Normalização da resposta
        # ==========================

        documents: List[Dict[str, Any]] = []

        try:
            # Converte o formato retornado pelo Pinecone
            # para o formato interno da aplicação
            for match in getattr(results, "matches", []):
                metadata = match.get("metadata", {}).copy()

                document = {
                    "id": match.get("id"),
                    "text": metadata.get("text", ""),
                    "metadata": metadata,
                    "score": match.get("score"),
                }

                # Remove o texto duplicado do metadata
                document["metadata"].pop("text", None)
                documents.append(document)

        except Exception as e:
            logger.exception("Failed to process search results.")
            raise RuntimeError("Failed to process search results.") from e

        return documents



    def get_all_docs_by_metadata(
        self,
        batch_size: int = 100,
        dimension: int = 3072,
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

        # Validação do filtro alvo
        if not target_value:
            raise ValueError("target_value cannot be empty.")

        # Proteção contra valores inválidos de paginação
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero.")

        # Vetor fictício necessário para satisfazer o contrato da API do Pinecone
        dummy_vector = [0.0] * dimension

        # Montagem dinâmica do filtro:
        # - valor único → $eq
        # - lista de valores → $in
        if isinstance(target_value, list):
            filter_query = {
                target_key: {"$in": target_value}
            }
        else:
            filter_query = {
                target_key: {"$eq": target_value}
            }

        results: List[Dict[str, Any]] = []
        pagination_token: Optional[str] = None

        try:
            # Loop de paginação explícita para garantir
            # a recuperação completa dos vetores
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

                # Normalização dos resultados retornados
                for match in response.get("matches", []):
                    results.append(
                        {
                            "id": match["id"],
                            "metadata": match.get("metadata", {}),
                            "score": match.get("score"),
                        }
                    )

                # Atualização do token de paginação
                pagination_token = (
                    response.get("pagination", {}) or {}
                ).get("next")

                # Encerramento do loop quando não há mais páginas
                if not pagination_token:
                    break

        except Exception as e:
            logger.exception(
                "Failed to retrieve vectors for %s=%s",
                target_key,
                target_value,
            )
            raise RuntimeError(
                "Failed to retrieve vectors by target."
            ) from e

        return results






import json

client = PineconeClient(
    namespace="betterai-embeddings-dev",
    embedding_model="text-embedding-3-large"
)

retriever = PineconeRetriever(client)

vectors = retriever.get_all_docs_by_metadata(
    target_value=["xxxxxx", "21d75dca2eec7b02080327f40220e20dxx2"]
)

print(len(vectors))

#print(f"\n\n{json.dumps(vectors, indent=4)}\n\n")

# python -m src.vector_store.pinecone_retriever
























