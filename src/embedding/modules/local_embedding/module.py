"""
LocalDynamicEmbedding
=====================

Pipeline local de chunking + embeddings + retrieval.

Novidades desta refatoração
---------------------------
1. Embeddings opcionais: se nenhum for informado, a própria classe usa
   `DeterministicFakeEmbedding(size=size)` — `size` é parâmetro da classe.
   Não é mais preciso instanciar os fake embeddings por fora.

2. Provedores em uma classe separada (`EmbeddingFactory`): `openai`,
   `huggingface`, `fake` e quaisquer outros que venham a existir ficam
   lá. A pipeline só chama `EmbeddingFactory.create(...)`.

3. API fluente (builder): dá para montar o fluxo passo a passo, um método
   para cada coisa, em vez de configurar tudo de uma vez:

       pipeline = (
           LocalDynamicEmbedding()
           .with_provider("openai", model="text-embedding-3-large")
           .with_splitter(chunk_size=3000, chunk_overlap=300)
           .with_top_k(5)
       )
       pipeline.process_text(texto)

4. Acesso aos chunks: cada chunk expõe texto, metadados e o vetor de
   embedding (a "lista de números"), além de tamanho e dimensão.
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
    """Um pedaço do texto com seu texto, metadados e embedding."""

    index: int
    content: str
    metadata: dict
    # o vetor de embedding (lista de números); repr=False p/ não poluir o print
    embedding: List[float] = field(default_factory=list, repr=False)

    @property
    def length(self) -> int:
        """Quantidade de caracteres do chunk."""
        return len(self.content)

    @property
    def dim(self) -> int:
        """Dimensionalidade do embedding."""
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
    Pipeline local de chunking + embeddings + retrieval.

    Parameters
    ----------
    embeddings:
        Instância de `Embeddings` do LangChain. Se `None`, a classe cria
        automaticamente `DeterministicFakeEmbedding(size=size)`.
    size:
        Dimensão usada pelos fake embeddings padrão. Default: 384.
    chunk_size / chunk_overlap:
        Parâmetros do text splitter.
    top_k:
        Número padrão de chunks retornados por consulta.
    separators:
        Separadores do RecursiveCharacterTextSplitter.
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
        """Injeta uma instância de `Embeddings` pronta."""
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
        """Usa fake embeddings (opcionalmente mudando o `size`)."""
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
        """Escolhe o provedor pela `EmbeddingFactory` (openai, huggingface...)."""
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
        """Configura o text splitter."""
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
        """Define o top_k padrão do retriever."""
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
        """Cria a pipeline já com o provedor escolhido."""
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
        Divide `text` em chunks, gera embeddings (uma única vez) e guarda
        tudo localmente. Pode ser chamado várias vezes (acumula).

        Returns
        -------
        int : quantidade de chunks gerados nesta chamada.
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
        Retorna os chunks mais relevantes para `query`.

        Cada item tem: `content`, `score`, `metadata` e, se
        `include_embedding=True`, também `embedding`.
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
        """Retorna um `VectorStoreRetriever` nativo do LangChain."""
        self._ensure_processed()
        kwargs.setdefault("search_kwargs", {"k": self.top_k})
        return self._vectorstore.as_retriever(**kwargs)

    # ------------------------------------------------------------------
    # Acesso aos chunks (texto + metadados + embeddings)
    # ------------------------------------------------------------------
    @property
    def chunks(self) -> List[Chunk]:
        """Lista de objetos `Chunk` (com content, metadata e embedding)."""
        return self._chunks

    def get_chunks(self, include_embedding: bool = True) -> List[dict]:
        """Mesma coisa em forma de dicionários (útil p/ serializar/JSON)."""
        return [c.to_dict(include_embedding=include_embedding) for c in self._chunks]

    def get_chunk(self, index: int) -> Optional[Chunk]:
        """Recupera um chunk específico pelo seu índice."""
        return self._index_map.get(index)

    @property
    def total_chunks(self) -> int:
        return len(self._chunks)

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------
    def _ensure_processed(self) -> None:
        if self._vectorstore is None:
            raise RuntimeError(
                "Nenhum texto foi processado ainda. Chame `process_text()` "
                "antes de consultar o Retriever."
            )

    def _guard_not_built(self, what: str) -> None:
        if self._vectorstore is not None:
            raise RuntimeError(
                f"Não é possível reconfigurar {what} depois de process_text(). "
                "Chame `clear()` primeiro."
            )

    def clear(self) -> "LocalDynamicEmbedding":
        self._vectorstore = None
        self._chunks = []
        self._index_map = {}
        return self
