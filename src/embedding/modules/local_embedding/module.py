"""
LocalDynamicEmbedding
=====================

Local pipeline for chunking, embeddings, and retrieval.

What's new in this refactor
---------------------------
1. Optional embeddings: if no embedding provider is specified, the class
automatically uses `DeterministicFakeEmbedding(size=size)`, where `size`
is a configurable class parameter. There is no longer any need to
instantiate fake embeddings externally.

2. Providers separated into `EmbeddingFactory`: embedding providers such
as `openai`, `huggingface`, `fake`, and any future implementations are
managed by `EmbeddingFactory`. The pipeline simply calls
`EmbeddingFactory.create(...)`.

3. Fluent API (Builder Pattern): build the pipeline step by step using
dedicated methods for each component, instead of configuring everything
at once.

Example:

pipeline = (
    LocalDynamicEmbedding()
    .with_provider("openai", model="text-embedding-3-large")
    .with_splitter(chunk_size=3000, chunk_overlap=300)
    .with_top_k(5)
)

pipeline.process_text(text)

4. Chunk inspection: each chunk provides access to its text, metadata,
embedding vector (the list of floating-point values), token count, and
embedding dimension.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

from dotenv import load_dotenv

from src.embedding.modules.local_embedding.embedding_factory import EmbeddingFactory 

load_dotenv()  # carrega variáveis de ambiente do .env, caso exista

DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


@dataclass
class Chunk:
    """
    Represents a text chunk along with its metadata and embedding vector.

    Args:
    :param index (int): The index position of the chunk in the original text.
    :param content (str): The text content of the chunk.
    :param metadata (dict): Metadata associated with the chunk.
    :param embedding (List[float]): The embedding vector for the chunk (default is an empty list).

    Properties:
        length: Returns the number of characters in the chunk.
        dim: Returns the dimension of the embedding vector.
        
    Methods:
        to_dict(): Returns the chunk data as a dictionary, with optional inclusion of the embedding vector.
    """

    index: int
    content: str
    metadata: dict
    # o vetor de embedding (lista de números); repr=False p/ não poluir o print
    embedding: List[float] = field(default_factory=list, repr=False)

    @property
    def length(self) -> int:
        return len(self.content)

    @property
    def dim(self) -> int:
        return len(self.embedding)

    def to_dict(self, include_embedding: bool = True) -> dict:
        data = {
            "index": self.index,
            "content": self.content,
            "metadata": self.metadata,
            "length": self.length,
            "dim": self.dim,
        }
        if include_embedding:
            data["embedding"] = self.embedding
        return data


class LocalDynamicEmbedding:
    """
    LocalDynamicEmbedding manages a local pipeline for text chunking, embedding computation, and retrieval.
    It supports different embedding providers via a fluent (builder) API, enabling flexible configuration
    of embeddings, text splitting parameters, and retrieval settings.

    Args:
    :param embeddings (Optional[Embeddings]): Custom embeddings instance (Default is None, which uses internal fake embeddings).
    :param size (int): Embedding size dimension, used when creating fake embeddings (Default is 384).
    :param chunk_size (int): Maximum size of each text chunk (Default is 500).
    :param chunk_overlap (int): Overlap size between chunks to keep context (Default is 50).
    :param top_k (int): Number of top results to return in retrieval (Default is 4).
    :param separators (Optional[List[str]]): List of separators for splitting text into chunks (Default uses predefined separators).

    Methods:
        with_embeddings(): Sets a custom embeddings instance to be used in the pipeline.
        with_fake_embeddings(): Configures the pipeline to use fake embeddings with optional size specification.
        with_provider(): Sets the embedding provider using a provider name and additional keyword arguments.
        with_splitter(): Configures the text splitter with chunk size, overlap, and separators.
        with_top_k(): Sets the number of top retrieval results to return.
        from_provider(): Classmethod to create an instance with specified provider and parameters.
        from_openai_embeddings(): Classmethod to configure with OpenAI embeddings.
        from_huggingface_embeddings(): Classmethod to configure with Huggingface embeddings.
        from_fake_embeddings(): Classmethod to configure with fake embeddings.
        process_text(): Processes input text by splitting, embedding, and storing chunks.
        retrieve(): Retrieves top matching chunks for a given query string.
        as_retriever(): Returns a VectorStoreRetriever for external query handling.
        get_chunks(): Returns a list of all chunks as dictionaries, optionally including embeddings.
        get_chunk(): Returns a single Chunk object by its index.
        clear(): Resets the pipeline state, clearing all processed data.
    """

    def __init__(
        self,
        embeddings: Optional[Embeddings] = None,
        size: int = 384,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        top_k: int = 4,
        separators: Optional[List[str]] = None,
    ) -> None:
        self.size = size
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k
        self.separators = (
            list(separators) if separators is not None else list(DEFAULT_SEPARATORS)
        )

        # Resolvidos de forma "lazy" para permitir reconfiguração fluente.
        self._embeddings: Optional[Embeddings] = embeddings
        self._splitter: Optional[RecursiveCharacterTextSplitter] = None

        # "Variável local" com chunks + embeddings (índice FAISS em memória).
        self._vectorstore: Optional[FAISS] = None
        self._chunks: List[Chunk] = []
        self._index_map: Dict[int, Chunk] = {}

    # ------------------------------------------------------------------
    # Propriedades lazy (só constroem quando realmente precisam)
    # ------------------------------------------------------------------
    @property
    def embeddings(self) -> Embeddings:
        try:
            if self._embeddings is None:
                # Default pedido: fake embeddings, sem precisar instanciar por fora.
                self._embeddings = EmbeddingFactory.fake(size=self.size)
            return self._embeddings
        except Exception as e:
            raise RuntimeError(
                f"Error creating embeddings. Check the parameters: size={self.size}. "
                f"Original error: {str(e)}"
            )

    @property
    def splitter(self) -> RecursiveCharacterTextSplitter:
        try:
            if self._splitter is None:
                self._splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                    separators=self.separators,
                )
            return self._splitter
        except Exception as e:
            raise RuntimeError(
                f"Error creating text splitter. Check the parameters: "
                f"chunk_size={self.chunk_size}, chunk_overlap={self.chunk_overlap}, separators={self.separators}. "
                f"Original error: {str(e)}"
            )

    # ------------------------------------------------------------------
    # API fluente (builder) – monte o fluxo passo a passo
    # ------------------------------------------------------------------
    def with_embeddings(self, embeddings: Embeddings) -> "LocalDynamicEmbedding":
        """
        Sets a custom embeddings instance for the pipeline, if not already built.

        Args:
            embeddings (Embeddings): Custom embeddings instance to set.

        Returns:
            LocalDynamicEmbedding: Returns self for fluent chaining.

        Raises:
            RuntimeError: If embeddings are set after processing started or if embeddings instance is invalid.
        """
        try:
            self._guard_not_built("embeddings")
            self._embeddings = embeddings
            return self
        except Exception as e:
            raise RuntimeError(
                f"Error setting embeddings. Ensure the embeddings instance: {str(embeddings)} is valid. "
            )

    def with_fake_embeddings(
        self, size: Optional[int] = None
    ) -> "LocalDynamicEmbedding":
        """
        Configures the pipeline to use fake embeddings, optionally setting the embedding size.

        Args:
            size (Optional[int]): Embedding vector size (Default uses existing or 384).

        Returns:
            LocalDynamicEmbedding: Returns self for fluent chaining.

        Raises:
            RuntimeError: If fake embeddings cannot be set due to invalid size or internal error.
        """
        try:
            self._guard_not_built("embeddings")
            if size is not None:
                self.size = size
            self._embeddings = EmbeddingFactory.fake(size=self.size)
            return self
        except Exception as e:
            raise RuntimeError(
                f"Error setting fake embeddings. Check the size parameter: {size}. "
                f"Original error: {str(e)}"
            )

    def with_provider(
        self, provider: str, **kwargs
    ) -> "LocalDynamicEmbedding":
        """
        Sets the embedding provider by name, with additional parameters.

        Args:
            provider (str): Name of the embedding provider (e.g., 'openai', 'huggingface', 'fake').
            **kwargs: Additional keyword arguments for the embedding provider.

        Returns:
            LocalDynamicEmbedding: Returns self for fluent chaining.

        Raises:
            RuntimeError: If provider cannot be set or instantiation fails.
        """
        try:
            self._guard_not_built("embeddings")
            self._embeddings = EmbeddingFactory.create(provider, **kwargs)
            return self
        except Exception as e:
            raise RuntimeError(
                f"Error setting provider '{provider}' with parameters {kwargs}. "
                f"Original error: {str(e)}"
            )

    def with_splitter(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        separators: Optional[List[str]] = None,
    ) -> "LocalDynamicEmbedding":
        """
        Configures the text splitter with chunk size, chunk overlap, and separators parameters.

        Args:
            chunk_size (Optional[int]): Maximum chunk size in characters.
            chunk_overlap (Optional[int]): Overlap size between chunks.
            separators (Optional[List[str]]): List of separators to use for splitting.

        Returns:
            LocalDynamicEmbedding: Returns self for fluent chaining.

        Raises:
            RuntimeError: If splitter parameters cannot be set due to prior processing or invalid inputs.
        """
        try:
            self._guard_not_built("splitter")
            if chunk_size is not None:
                self.chunk_size = chunk_size
            if chunk_overlap is not None:
                self.chunk_overlap = chunk_overlap
            if separators is not None:
                self.separators = list(separators)
            self._splitter = None  # força reconstrução com os novos valores
            return self
        except Exception as e:
            raise RuntimeError(
                f"Error setting splitter parameters: chunk_size={chunk_size}, "
                f"chunk_overlap={chunk_overlap}, separators={separators}. "
                f"Original error: {str(e)}"
            )

    def with_top_k(self, top_k: int) -> "LocalDynamicEmbedding":
        """
        Sets the 'top_k' parameter indicating how many top results to retrieve.

        Args:
            top_k (int): Number of top retrieval results to return.

        Returns:
            LocalDynamicEmbedding: Returns self for fluent chaining.
        """
        self.top_k = top_k
        return self

    # ------------------------------------------------------------------
    # Classmethods de conveniência (delegam para a EmbeddingFactory)
    # ------------------------------------------------------------------
    @classmethod
    def from_provider(
        cls,
        provider: str = "fake",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        top_k: int = 4,
        separators: Optional[List[str]] = None,
        **provider_kwargs,
    ) -> "LocalDynamicEmbedding":
        """
        Creates a LocalDynamicEmbedding instance configured from a specified embedding provider.

        Args:
            provider (str): Embedding provider name (default "fake").
            chunk_size (int): Chunk size for text splitting.
            chunk_overlap (int): Overlap size for chunks.
            top_k (int): Number of top results to retrieve.
            separators (Optional[List[str]]): List of splitting separators.
            **provider_kwargs: Additional parameters for the embedding provider.

        Returns:
            LocalDynamicEmbedding: Configured instance.
        """
        return cls(
            embeddings=EmbeddingFactory.create(provider, **provider_kwargs),
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            top_k=top_k,
            separators=separators,
        )

    @classmethod
    def from_openai_embeddings(
        cls,
        model: str = "text-embedding-3-large",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        top_k: int = 4,
        separators: Optional[List[str]] = None,
        **kwargs,
    ) -> "LocalDynamicEmbedding":
        """
        Creates an instance configured to use OpenAI embeddings.

        Args:
            model (str): Model identifier (default "text-embedding-3-large").
            chunk_size (int): Chunk size for splitting.
            chunk_overlap (int): Overlap size between chunks.
            top_k (int): Number of top results to retrieve.
            separators (Optional[List[str]]): List of separators for splitting.
            **kwargs: Additional provider-specific parameters.

        Returns:
            LocalDynamicEmbedding: Configured instance with OpenAI embeddings.
        """
        return cls.from_provider(
            "openai",
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            top_k=top_k,
            separators=separators,
            model=model,
            **kwargs,
        )

    @classmethod
    def from_huggingface_embeddings(
        cls,
        model: str = "sentence-transformers/all-MiniLM-L6-v2",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        top_k: int = 4,
        separators: Optional[List[str]] = None,
        **kwargs,
    ) -> "LocalDynamicEmbedding":
        """
        Creates an instance configured to use Huggingface embeddings.

        Args:
            model (str): Model identifier (default "sentence-transformers/all-MiniLM-L6-v2").
            chunk_size (int): Chunk size for splitting.
            chunk_overlap (int): Overlap size between chunks.
            top_k (int): Number of top results to retrieve.
            separators (Optional[List[str]]): List of separators for splitting.
            **kwargs: Additional provider-specific parameters.

        Returns:
            LocalDynamicEmbedding: Configured instance with Huggingface embeddings.
        """
        return cls.from_provider(
            "huggingface",
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            top_k=top_k,
            separators=separators,
            model=model,
            **kwargs,
        )

    @classmethod
    def from_fake_embeddings(
        cls,
        size: int = 384,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        top_k: int = 4,
        separators: Optional[List[str]] = None,
    ) -> "LocalDynamicEmbedding":
        """
        Creates an instance configured to use fake embeddings with specified size.

        Args:
            size (int): Embedding vector size (default 384).
            chunk_size (int): Chunk size for splitting.
            chunk_overlap (int): Overlap size between chunks.
            top_k (int): Number of top results to retrieve.
            separators (Optional[List[str]]): List of separators for splitting.

        Returns:
            LocalDynamicEmbedding: Configured instance with fake embeddings.
        """
        return cls(
            embeddings=EmbeddingFactory.fake(size=size),
            size=size,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            top_k=top_k,
            separators=separators,
        )

    # ------------------------------------------------------------------
    # Cenário 1 – Processamento do texto
    # ------------------------------------------------------------------
    def process_text(self, text: str, metadata: Optional[dict] = None) -> int:
        """
        Splits the input text into chunks, computes embeddings for each chunk,
        stores them, and adds them to a FAISS vector store for retrieval.

        Args:
            text (str): The input text to process (must be non-empty).
            metadata (Optional[dict]): Optional metadata to associate with all chunks.

        Returns:
            int: The number of chunks created and processed.

        Raises:
            RuntimeError: If input text is empty or processing fails.
        """
        try:
            if not text or not text.strip():
                raise ValueError("O texto de entrada não pode ser vazio.")

            raw_chunks = self.splitter.split_text(text)
            base_metadata = dict(metadata or {})

            texts: List[str] = []
            metadatas: List[dict] = []
            for i, chunk in enumerate(raw_chunks):
                md = dict(base_metadata)
                md["chunk_index"] = len(self._chunks) + i
                texts.append(chunk)
                metadatas.append(md)

            # Calcula os embeddings uma vez só e reaproveita para o FAISS.
            vectors = self.embeddings.embed_documents(texts)

            for txt, md, vec in zip(texts, metadatas, vectors):
                chunk_obj = Chunk(
                    index=md["chunk_index"],
                    content=txt,
                    metadata=md,
                    embedding=[float(x) for x in vec],
                )
                self._chunks.append(chunk_obj)
                self._index_map[chunk_obj.index] = chunk_obj

            text_embeddings = list(zip(texts, vectors))
            if self._vectorstore is None:
                self._vectorstore = FAISS.from_embeddings(
                    text_embeddings=text_embeddings,
                    embedding=self.embeddings,
                    metadatas=metadatas,
                )
            else:
                self._vectorstore.add_embeddings(
                    text_embeddings=text_embeddings, metadatas=metadatas
                )

            return len(texts)
        except Exception as e:
            raise RuntimeError(
                f"Error processing text: {str(e)}"
            )

    # ------------------------------------------------------------------
    # Cenário 2 – Recuperação de conteúdo (Retriever)
    # ------------------------------------------------------------------
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        include_embedding: bool = False,
    ) -> List[Dict]:
        """
        Retrieves the top matching text chunks for a given query using similarity search.

        Args:
            query (str): The query string to search for.
            top_k (Optional[int]): Number of top results to return (defaults to class's top_k).
            include_embedding (bool): Whether to include the embedding vector in the returned results.

        Returns:
            List[Dict]: A list of dictionaries containing chunk content, score, metadata,
                        and optionally embedding vectors.

        Raises:
            RuntimeError: If retrieval fails or no data has been processed yet.
        """
        try:
            self._ensure_processed()

            k = top_k or self.top_k
            results = self._vectorstore.similarity_search_with_score(query, k=k)

            formatted_results: List[Dict] = []
            for doc, score in results:
                item = {
                    "content": doc.page_content.strip(),
                    "score": float(score),
                    "metadata": doc.metadata,
                }
                if include_embedding:
                    chunk = self._index_map.get(doc.metadata.get("chunk_index"))
                    item["embedding"] = chunk.embedding if chunk else None
                formatted_results.append(item)

            return formatted_results
        except Exception as e:
            raise RuntimeError(
                f"Error retrieving results for query '{query}': {str(e)}"
            )

    def as_retriever(self, **kwargs) -> VectorStoreRetriever:
        """
        Returns a VectorStoreRetriever instance configured with the stored embeddings,
        allowing external components to perform retrieval queries.

        Args:
            **kwargs: Additional keyword arguments for the retriever configuration.

        Returns:
            VectorStoreRetriever: Retriever instance for querying the vector store.

        Raises:
            RuntimeError: If no text has been processed yet.
        """
        self._ensure_processed()
        kwargs.setdefault("search_kwargs", {"k": self.top_k})
        return self._vectorstore.as_retriever(**kwargs)

    # ------------------------------------------------------------------
    # Acesso aos chunks (texto + metadados + embeddings)
    # ------------------------------------------------------------------
    @property
    def chunks(self) -> List[Chunk]:
        """Returns the list of stored Chunk objects."""
        return self._chunks

    def get_chunks(self, include_embedding: bool = True) -> List[dict]:
        """
        Returns all stored chunks as a list of dictionaries.

        Args:
            include_embedding (bool): Whether to include the embedding vector in each chunk dict.

        Returns:
            List[dict]: List of chunk information dictionaries.
        """
        return [c.to_dict(include_embedding=include_embedding) for c in self._chunks]

    def get_chunk(self, index: int) -> Optional[Chunk]:
        """
        Retrieves a single chunk by its index.

        Args:
            index (int): The index of the desired chunk.

        Returns:
            Optional[Chunk]: The Chunk object if found, otherwise None.
        """
        return self._index_map.get(index)

    @property
    def total_chunks(self) -> int:
        """Returns the total number of stored chunks."""
        return len(self._chunks)

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------
    def _ensure_processed(self) -> None:
        """
        Ensures that text has been processed before retrieval.

        Raises:
            RuntimeError: If no text has been processed yet.
        """
        if self._vectorstore is None:
            raise RuntimeError(
                "Nenhum texto foi processado ainda. Chame `process_text()` "
                "antes de consultar o Retriever."
            )

    def _guard_not_built(self, what: str) -> None:
        """
        Prevents reconfiguration of components after the pipeline has processed text.

        Args:
            what (str): The component name to guard (e.g., 'embeddings', 'splitter').

        Raises:
            RuntimeError: If the component is attempted to be changed after processing.
        """
        if self._vectorstore is not None:
            raise RuntimeError(
                f"Não é possível reconfigurar {what} depois de process_text(). "
                "Chame `clear()` primeiro."
            )

    def clear(self) -> "LocalDynamicEmbedding":
        """
        Clears all stored chunks, embeddings, and the vector store, allowing the pipeline
        to be reconfigured and reused.

        Returns:
            LocalDynamicEmbedding: Returns self for fluent chaining.
        """
        self._vectorstore = None
        self._chunks = []
        self._index_map = {}
        return self
