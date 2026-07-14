"""
EmbeddingFactory
================

Separate class responsible for building `Embeddings` instances.
Centralizes all logic for "which provider to use" so that
`LocalDynamicEmbedding` does not need to know the details of each
library.

Built-in providers:
- "fake"         -> DeterministicFakeEmbedding (100% local, no model,
                    ideal for testing/development).
- "huggingface"  -> HuggingFaceEmbeddings (sentence-transformers).
- "openai"       -> OpenAIEmbeddings.

New providers can be added without editing this class, via
`EmbeddingFactory.register("name", builder)`.
"""

from __future__ import annotations

from typing import Callable, Dict, List

from langchain_core.embeddings import Embeddings

try:  # current location
    from langchain_core.embeddings import DeterministicFakeEmbedding
except ImportError:  # older versions of langchain-core
    from langchain_core.embeddings.fake import DeterministicFakeEmbedding


class EmbeddingSetupError(ImportError):
    """Friendly error raised when a provider dependency is missing."""


class EmbeddingFactory:
    # Extra providers registered at runtime (name -> builder)
    _EXTRA: Dict[str, Callable[..., Embeddings]] = {}

    # ------------------------------------------------------------------
    # Built-in providers
    # ------------------------------------------------------------------
    @staticmethod
    def fake(size: int = 384, **kwargs) -> Embeddings:
        """Deterministic fake embeddings (no model, no network)."""
        return DeterministicFakeEmbedding(size=size, **kwargs)

    @staticmethod
    def huggingface(
        model: str = "sentence-transformers/all-MiniLM-L6-v2", **kwargs
    ) -> Embeddings:
        """Local embeddings via sentence-transformers."""
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
        except ImportError as exc:  # pragma: no cover
            raise EmbeddingSetupError(
                "To use HuggingFace, install 'sentence-transformers' "
                "(pip install sentence-transformers)."
            ) from exc
        return HuggingFaceEmbeddings(model_name=model, **kwargs)

    @staticmethod
    def openai(model: str = "text-embedding-3-large", **kwargs) -> Embeddings:
        """Embeddings via OpenAI (requires OPENAI_API_KEY)."""
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError as exc:  # pragma: no cover
            raise EmbeddingSetupError(
                "To use OpenAIEmbeddings, install 'langchain-openai' "
                "(pip install langchain-openai) and set OPENAI_API_KEY."
            ) from exc
        return OpenAIEmbeddings(model=model, **kwargs)

    # ------------------------------------------------------------------
    # Registration / dispatch
    # ------------------------------------------------------------------
    @classmethod
    def register(
        cls, name: str, builder: Callable[..., Embeddings]
    ) -> Callable[..., Embeddings]:
        """Registers (or overwrites) a provider at runtime.

        Example:
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
        """Returns a sorted list of all available providers."""
        return sorted(cls._builders())

    @classmethod
    def create(cls, provider: str = "fake", **kwargs) -> Embeddings:
        """Creates an `Embeddings` instance for the requested provider.

        `provider` is case-insensitive and `**kwargs` are forwarded to
        the builder (e.g.: `size` for fake, `model` for openai/huggingface).
        """
        key = provider.lower()
        builders = cls._builders()
        if key not in builders:
            raise ValueError(
                f"Provider '{provider}' is not supported. "
                f"Available: {sorted(builders)}"
            )
        return builders[key](**kwargs)