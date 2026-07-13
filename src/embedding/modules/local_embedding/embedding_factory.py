"""
EmbeddingFactory
================

Classe separada, responsável por construir instâncias de `Embeddings`.
Centraliza toda a lógica de "qual provedor usar" para que a
`LocalDynamicEmbedding` não precise conhecer os detalhes de cada
biblioteca.

Provedores nativos:
- "fake"         -> DeterministicFakeEmbedding (100% local, sem modelo,
                    ideal para testes/desenvolvimento).
- "huggingface"  -> HuggingFaceEmbeddings (sentence-transformers).
- "openai"       -> OpenAIEmbeddings.

Novos provedores podem ser adicionados sem editar esta classe, via
`EmbeddingFactory.register("nome", builder)`.
"""

from __future__ import annotations

from typing import Callable, Dict, List

from langchain_core.embeddings import Embeddings

try:  # localização atual
    from langchain_core.embeddings import DeterministicFakeEmbedding
except ImportError:  # versões mais antigas do langchain-core
    from langchain_core.embeddings.fake import DeterministicFakeEmbedding


class EmbeddingSetupError(ImportError):
    """Erro amigável quando falta uma dependência de um provedor."""


class EmbeddingFactory:
    # Provedores extras registrados em runtime (nome -> builder)
    _EXTRA: Dict[str, Callable[..., Embeddings]] = {}

    # ------------------------------------------------------------------
    # Provedores nativos
    # ------------------------------------------------------------------
    @staticmethod
    def fake(size: int = 384, **kwargs) -> Embeddings:
        """Embeddings falsos determinísticos (sem modelo, sem rede)."""
        return DeterministicFakeEmbedding(size=size, **kwargs)

    @staticmethod
    def huggingface(
        model: str = "sentence-transformers/all-MiniLM-L6-v2", **kwargs
    ) -> Embeddings:
        """Embeddings locais via sentence-transformers."""
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
        except ImportError as exc:  # pragma: no cover
            raise EmbeddingSetupError(
                "Para usar HuggingFace, instale 'sentence-transformers' "
                "(pip install sentence-transformers)."
            ) from exc
        return HuggingFaceEmbeddings(model_name=model, **kwargs)

    @staticmethod
    def openai(model: str = "text-embedding-3-large", **kwargs) -> Embeddings:
        """Embeddings via OpenAI (requer OPENAI_API_KEY)."""
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError as exc:  # pragma: no cover
            raise EmbeddingSetupError(
                "Para usar OpenAIEmbeddings, instale 'langchain-openai' "
                "(pip install langchain-openai) e configure OPENAI_API_KEY."
            ) from exc
        return OpenAIEmbeddings(model=model, **kwargs)

    # ------------------------------------------------------------------
    # Registro / dispatch
    # ------------------------------------------------------------------
    @classmethod
    def register(
        cls, name: str, builder: Callable[..., Embeddings]
    ) -> Callable[..., Embeddings]:
        """Registra (ou sobrescreve) um provedor em runtime.

        Exemplo:
            EmbeddingFactory.register("cohere", lambda **kw: CohereEmbeddings(**kw))
        """
        cls._EXTRA[name.lower()] = builder
        return builder

    @classmethod
    def _builders(cls) -> Dict[str, Callable[..., Embeddings]]:
        return {
            "fake": cls.fake,
            "huggingface": cls.huggingface,
            "openai": cls.openai,
            **cls._EXTRA,
        }

    @classmethod
    def available(cls) -> List[str]:
        """Lista todos os provedores disponíveis."""
        return sorted(cls._builders())

    @classmethod
    def create(cls, provider: str = "fake", **kwargs) -> Embeddings:
        """Cria a instância de `Embeddings` do provedor pedido.

        `provider` é case-insensitive e os `**kwargs` são repassados ao
        builder (ex.: `size` para fake, `model` para openai/huggingface).
        """
        key = provider.lower()
        builders = cls._builders()
        if key not in builders:
            raise ValueError(
                f"Provider '{provider}' não suportado. "
                f"Disponíveis: {sorted(builders)}"
            )
        return builders[key](**kwargs)