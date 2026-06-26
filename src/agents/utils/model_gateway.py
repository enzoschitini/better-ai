
import inspect
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from dotenv import load_dotenv

from agno.agent import Agent

from agno.models.anthropic.claude import Claude
from agno.models.google.gemini import Gemini
from agno.models.groq.groq import Groq
from agno.models.openai.chat import OpenAIChat
from agno.models.openai.like import OpenAILike
from agno.models.openai.open_responses import OpenResponses
from agno.models.openai.responses import OpenAIResponses

load_dotenv()


class ModelGateway:
    """
    Unified and provider-aware model factory for Agno models.

    Supports providers:
    - Anthropic -> Claude
    - Google -> Gemini
    - Groq -> Groq
    - OpenAI -> OpenAIChat, OpenAIResponses, OpenResponses, OpenAILike

    Main goals:
    - Complete parameter support: any constructor parameter from the target model class can be passed.
    - Intuitive API: one `create_model` and one `create_agent` entrypoint, plus convenience methods.
    - Safe usage: optional strict validation for unknown parameters.
    """

    _MODEL_FACTORIES: Dict[str, Callable[..., Any]] = {
        "anthropic": Claude,
        "google": Gemini,
        "groq": Groq,
        "openai.chat": OpenAIChat,
        "openai.responses": OpenAIResponses,
        "openai.open_responses": OpenResponses,
        "openai.like": OpenAILike,
    }

    _PROVIDER_ALIASES: Dict[str, str] = {
        "anthropic": "anthropic",
        "claude": "anthropic",
        "google": "google",
        "gemini": "google",
        "groq": "groq",
        "openai": "openai",
        "open_ai": "openai",
    }

    _OPENAI_VARIANT_ALIASES: Dict[str, str] = {
        "chat": "chat",
        "openai_chat": "chat",
        "responses": "responses",
        "openai_responses": "responses",
        "open_responses": "open_responses",
        "openresponses": "open_responses",
        "like": "like",
        "openai_like": "like",
    }

    def __init__(self, strict_validation: bool = True) -> None:
        self.strict_validation = strict_validation

    @classmethod
    def supported_providers(cls) -> Sequence[str]:
        return ("anthropic", "google", "groq", "openai")

    @classmethod
    def supported_openai_variants(cls) -> Sequence[str]:
        return ("chat", "responses", "open_responses", "like")

    def supported_parameters(self, provider: str, openai_variant: str = "chat") -> List[str]:
        factory_key = self._resolve_factory_key(provider=provider, openai_variant=openai_variant)
        return self._get_constructor_param_names(factory_key)

    def create_model(
        self,
        provider: str,
        model_id: Optional[str] = None,
        *,
        openai_variant: str = "chat",
        strict_validation: Optional[bool] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Creates and returns an Agno model instance from the selected provider.

        Args:
            provider: One of `anthropic`, `google`, `groq`, `openai`.
            model_id: Optional model id. If passed, overrides `id` in kwargs.
            openai_variant: OpenAI family model class. One of
                `chat`, `responses`, `open_responses`, `like`.
            strict_validation: Overrides instance-level strict validation.
            **kwargs: Any constructor parameter accepted by the selected class.
        """
        factory_key = self._resolve_factory_key(provider=provider, openai_variant=openai_variant)
        constructor_kwargs = dict(kwargs)
        if model_id is not None:
            constructor_kwargs["id"] = model_id

        should_validate = self.strict_validation if strict_validation is None else strict_validation
        if should_validate:
            self._validate_kwargs(factory_key, constructor_kwargs)

        factory = self._MODEL_FACTORIES[factory_key]
        return factory(**constructor_kwargs)

    def create_agent(
        self,
        provider: str,
        model_id: Optional[str] = None,
        *,
        openai_variant: str = "chat",
        model_kwargs: Optional[Dict[str, Any]] = None,
        **agent_kwargs: Any,
    ) -> Agent:
        """
        Creates an `agno.agent.Agent` with the selected provider model.

        Args:
            provider: One of `anthropic`, `google`, `groq`, `openai`.
            model_id: Optional model id.
            openai_variant: OpenAI family model class.
            model_kwargs: Optional constructor params for model creation.
            **agent_kwargs: Extra kwargs forwarded to `Agent(...)`.
        """
        model = self.create_model(
            provider=provider,
            model_id=model_id,
            openai_variant=openai_variant,
            **(model_kwargs or {}),
        )
        return Agent(model=model, **agent_kwargs)

    def anthropic(self, model_id: Optional[str] = None, **kwargs: Any) -> Claude:
        return self.create_model(provider="anthropic", model_id=model_id, **kwargs)

    def google(self, model_id: Optional[str] = None, **kwargs: Any) -> Gemini:
        return self.create_model(provider="google", model_id=model_id, **kwargs)

    def groq(self, model_id: Optional[str] = None, **kwargs: Any) -> Groq:
        return self.create_model(provider="groq", model_id=model_id, **kwargs)

    def openai_chat(self, model_id: Optional[str] = None, **kwargs: Any) -> OpenAIChat:
        return self.create_model(
            provider="openai",
            model_id=model_id,
            openai_variant="chat",
            **kwargs,
        )

    def openai_responses(self, model_id: Optional[str] = None, **kwargs: Any) -> OpenAIResponses:
        return self.create_model(
            provider="openai",
            model_id=model_id,
            openai_variant="responses",
            **kwargs,
        )

    def open_responses(self, model_id: Optional[str] = None, **kwargs: Any) -> OpenResponses:
        return self.create_model(
            provider="openai",
            model_id=model_id,
            openai_variant="open_responses",
            **kwargs,
        )

    def openai_like(self, model_id: Optional[str] = None, **kwargs: Any) -> OpenAILike:
        return self.create_model(
            provider="openai",
            model_id=model_id,
            openai_variant="like",
            **kwargs,
        )

    def _resolve_factory_key(self, provider: str, openai_variant: str = "chat") -> str:
        provider_key = (provider or "").strip().lower()
        normalized_provider = self._PROVIDER_ALIASES.get(provider_key)

        if normalized_provider is None:
            raise ValueError(
                f"Unsupported provider '{provider}'. Supported providers: {list(self.supported_providers())}"
            )

        if normalized_provider != "openai":
            return normalized_provider

        variant_key = (openai_variant or "").strip().lower()
        normalized_variant = self._OPENAI_VARIANT_ALIASES.get(variant_key)
        if normalized_variant is None:
            raise ValueError(
                "Unsupported openai_variant "
                f"'{openai_variant}'. Supported variants: {list(self.supported_openai_variants())}"
            )

        return f"openai.{normalized_variant}"

    def _get_constructor_param_names(self, factory_key: str) -> List[str]:
        constructor = self._MODEL_FACTORIES[factory_key]
        signature = inspect.signature(constructor.__init__)
        return [name for name in signature.parameters if name != "self"]

    def _validate_kwargs(self, factory_key: str, kwargs: Dict[str, Any]) -> None:
        valid_params = set(self._get_constructor_param_names(factory_key))
        invalid_params = sorted([key for key in kwargs.keys() if key not in valid_params])

        if invalid_params:
            raise ValueError(
                f"Invalid parameters for '{factory_key}': {invalid_params}. "
                f"Allowed parameters: {sorted(valid_params)}"
            )


if __name__ == "__main__":
    gateway = ModelGateway(strict_validation=True)

    # Example 1: OpenAI chat model
    chat_model = gateway.create_model(
        provider="openai",
        openai_variant="chat",
        model_id="gpt-4.1-mini",
        temperature=0.2,
    )

    # Example 2: Build agent directly from the unified gateway
    agent = gateway.create_agent(
        provider="openai",
        openai_variant="chat",
        model_kwargs={"id": "gpt-4.1-mini", "temperature": 0.2},
        markdown=True,
    )

    _ = chat_model
    agent.print_response("Ciao!")

    # python -m src.agents.utils.model_gateway