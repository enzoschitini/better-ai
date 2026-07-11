"""
LocalDynamicEmbedding
======================

Encapsula o fluxo descrito na task:
  1. Recebe um texto de entrada.
  2. Divide o texto em chunks (text splitting).
  3. Gera embeddings para cada chunk.
  4. Armazena chunks + embeddings em uma variável local (in-memory).
  5. Expõe um método Retriever que, dada uma consulta, retorna os
     chunks mais relevantes por similaridade semântica.

Decisões de design (referentes aos "Pontos a definir" da task)
----------------------------------------------------------------
- Text splitting: RecursiveCharacterTextSplitter (LangChain), que tenta
  quebrar por parágrafo -> linha -> frase -> palavra, nessa ordem,
  preservando o máximo de contexto possível. `chunk_size` e
  `chunk_overlap` são parametrizáveis.
- Embeddings: por padrão, um modelo local do sentence-transformers
  (`sentence-transformers/all-MiniLM-L6-v2`) via HuggingFaceEmbeddings,
  rodando 100% localmente (sem chamadas a API externa) — condizente com
  o nome "LocalDynamicEmbedding". Qualquer outro objeto compatível com a
  interface `Embeddings` do LangChain (ex: OpenAIEmbeddings) pode ser
  injetado via parâmetro `embeddings`, tornando o comportamento
  "dinâmico"/plugável.
- Armazenamento local: um índice FAISS in-memory (`self._vectorstore`),
  mantido apenas na instância da classe (variável local), sem
  persistência em disco por padrão.
- top_k: parametrizável no construtor (default 4) e sobrescrevível a
  cada chamada de `retrieve`.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

from dotenv import load_dotenv

load_dotenv()  # carrega variáveis de ambiente do .env, caso exista

class LocalDynamicEmbedding:
    """
    Pipeline local de chunking + embeddings + retrieval.

    Parameters
    ----------
    embeddings:
        Instância de `Embeddings` do LangChain a ser usada. Se `None`,
        instancia automaticamente `HuggingFaceEmbeddings` com o modelo
        indicado em `embedding_model` (requer o pacote
        `sentence-transformers` instalado).
    embedding_model:
        Nome do modelo do sentence-transformers usado quando `embeddings`
        não é informado. Default: "sentence-transformers/all-MiniLM-L6-v2".
    chunk_size:
        Tamanho máximo (em caracteres) de cada chunk.
    chunk_overlap:
        Sobreposição entre chunks consecutivos, para preservar contexto
        entre as bordas.
    top_k:
        Número padrão de chunks retornados por consulta no Retriever.
    """

    def __init__(
        self,
        embeddings: Optional[Embeddings] = None,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        top_k: int = 4,
    ) -> None:
        self.embedding_model_name = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k

        self._embeddings: Embeddings = embeddings or self._build_default_embeddings(
            embedding_model
        )

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        # "Variável local" que guarda chunks e embeddings (índice FAISS
        # em memória) exigida no critério de aceite do Cenário 1.
        self._vectorstore: Optional[FAISS] = None
        self._chunks: List[Document] = []

    # ------------------------------------------------------------------
    # Builders auxiliares
    # ------------------------------------------------------------------
    @classmethod
    def from_openai_embeddings(
        cls,
        model: str = "text-embedding-3-large",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        top_k: int = 4,
        **kwargs,
    ) -> "LocalDynamicEmbedding":
        """Cria uma instância usando `OpenAIEmbeddings`.

        Requer `langchain-openai` instalado e a variável de ambiente
        `OPENAI_API_KEY` configurada.
        """
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "Para usar OpenAIEmbeddings, instale 'langchain-openai' "
                "(pip install langchain-openai) e configure OPENAI_API_KEY."
            ) from exc

        embeddings = OpenAIEmbeddings(model=model, **kwargs)
        return cls(
            embeddings=embeddings,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            top_k=top_k,
        )

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------
    @staticmethod
    def _build_default_embeddings(embedding_model: str) -> Embeddings:
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "Para usar o modelo de embeddings local padrão, instale "
                "'sentence-transformers' (pip install sentence-transformers) "
                "ou injete sua própria instância via o parâmetro `embeddings`."
            ) from exc
        return HuggingFaceEmbeddings(model_name=embedding_model)

    # ------------------------------------------------------------------
    # Cenário 1 – Processamento do texto
    # ------------------------------------------------------------------
    def process_text(self, text: str, metadata: Optional[dict] = None) -> int:
        """
        Divide `text` em chunks, gera embeddings para cada chunk e
        acumula tudo na variável local (`self._vectorstore`).

        Pode ser chamado múltiplas vezes: novos textos são adicionados
        ao índice já existente.

        Returns
        -------
        int
            Quantidade de chunks gerados nesta chamada.
        """
        if not text or not text.strip():
            raise ValueError("O texto de entrada não pode ser vazio.")

        raw_chunks = self._splitter.split_text(text)
        base_metadata = dict(metadata or {})
        documents = []

        for index, chunk in enumerate(raw_chunks):
            doc_metadata = dict(base_metadata)
            doc_metadata["chunk_index"] = len(self._chunks) + index
            documents.append(
                Document(page_content=chunk, metadata=doc_metadata)
            )

        if self._vectorstore is None:
            self._vectorstore = FAISS.from_documents(documents, self._embeddings)
        else:
            self._vectorstore.add_documents(documents)

        self._chunks.extend(documents)
        return len(documents)

    # ------------------------------------------------------------------
    # Cenário 2 – Recuperação de conteúdo (Retriever)
    # ------------------------------------------------------------------
    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict]:
        """
        Consulta os embeddings armazenados e retorna os chunks mais
        relevantes com base na similaridade semântica com `query`.

        Returns
        -------
        list[dict]
            Cada item contém: `content` (texto do chunk), `score`
            (distância/similaridade) e `metadata`.
        """
        self._ensure_processed()

        k = top_k or self.top_k
        results = self._vectorstore.similarity_search_with_score(query, k=k)

        formatted_results = []
        for doc, score in results:
            content = doc.page_content.strip()

            """
            if len(content) < 220:
                context = content
            else:
                context = content[:220].rstrip() + "..."
            """

            formatted_results.append(
                {
                    "content": content,
                    "score": float(score),
                    "metadata": doc.metadata,
                }
            )

        return formatted_results

    def as_retriever(self, **kwargs) -> VectorStoreRetriever:
        """
        Retorna um Retriever nativo do LangChain (`VectorStoreRetriever`),
        pronto para ser usado em chains como `RetrievalQA` ou
        `create_retrieval_chain`.
        """
        self._ensure_processed()
        kwargs.setdefault("search_kwargs", {"k": self.top_k})
        return self._vectorstore.as_retriever(**kwargs)

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------
    def _ensure_processed(self) -> None:
        if self._vectorstore is None:
            raise RuntimeError(
                "Nenhum texto foi processado ainda. Chame `process_text()` "
                "antes de consultar o Retriever."
            )

    @property
    def total_chunks(self) -> int:
        return len(self._chunks)

    def clear(self) -> None:
        """Remove todos os chunks/embeddings armazenados localmente."""
        self._vectorstore = None
        self._chunks = []


# python -m src.embedding.modules.local_embedding