```python
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

    Args: 
    :param strict_validation (bool): Flag to enable strict validation of parameters. Default is True.

    Methods:
            supported_providers(): Returns a sequence of supported providers.
            supported_openai_variants(): Returns a sequence of supported OpenAI variants.
            supported_parameters(provider, openai_variant='chat'): Returns a list of valid constructor parameters for the specified provider and OpenAI variant.
            create_model(provider, model_id=None, *, openai_variant='chat', strict_validation=None, **kwargs): Creates and returns an Agno model instance from the selected provider.
            create_agent(provider, model_id=None, *, openai_variant='chat', model_kwargs=None, **agent_kwargs): Creates an agno.agent.Agent with the selected provider model.
            anthropic(model_id=None, **kwargs): Convenience method to create an Anthropic Claude model.
            google(model_id=None, **kwargs): Convenience method to create a Google Gemini model.
            groq(model_id=None, **kwargs): Convenience method to create a Groq model.
            openai_chat(model_id=None, **kwargs): Convenience method to create an OpenAIChat model.
            openai_responses(model_id=None, **kwargs): Convenience method to create an OpenAIResponses model.
            open_responses(model_id=None, **kwargs): Convenience method to create an OpenResponses model.
            openai_like(model_id=None, **kwargs): Convenience method to create an OpenAILike model.
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
        """
        Returns a sequence of supported providers.

        Returns:
                Sequence[str]: Supported model providers.
        """
        return ("anthropic", "google", "groq", "openai")

    @classmethod
    def supported_openai_variants(cls) -> Sequence[str]:
        """
        Returns a sequence of supported OpenAI model variants.

        Returns:
                Sequence[str]: Supported OpenAI model variants.
        """
        return ("chat", "responses", "open_responses", "like")

    def supported_parameters(self, provider: str, openai_variant: str = "chat") -> List[str]:
        """
        Returns a list of valid constructor parameter names for the specified provider and OpenAI variant.

        Args:
            provider (str): The model provider name.
            openai_variant (str): The OpenAI variant name. Default is "chat".

        Returns:
                List[str]: List of valid parameter names for the model constructor.
        """
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

        Returns:
                Agent: An agent instance configured with the selected model.
        """
        model = self.create_model(
            provider=provider,
            model_id=model_id,
            openai_variant=openai_variant,
            **(model_kwargs or {}),
        )
        return Agent(model=model, **agent_kwargs)

    def anthropic(self, model_id: Optional[str] = None, **kwargs: Any) -> Claude:
        """
        Creates an Anthropic Claude model instance.

        Args:
            model_id (Optional[str]): Optional model id. Default is None.
            **kwargs: Additional parameters passed to the Claude constructor.

        Returns:
                Claude: An instance of the Claude model.
        """
        return self.create_model(provider="anthropic", model_id=model_id, **kwargs)

    def google(self, model_id: Optional[str] = None, **kwargs: Any) -> Gemini:
        """
        Creates a Google Gemini model instance.

        Args:
            model_id (Optional[str]): Optional model id. Default is None.
            **kwargs: Additional parameters passed to the Gemini constructor.

        Returns:
                Gemini: An instance of the Gemini model.
        """
        return self.create_model(provider="google", model_id=model_id, **kwargs)

    def groq(self, model_id: Optional[str] = None, **kwargs: Any) -> Groq:
        """
        Creates a Groq model instance.

        Args:
            model_id (Optional[str]): Optional model id. Default is None.
            **kwargs: Additional parameters passed to the Groq constructor.

        Returns:
                Groq: An instance of the Groq model.
        """
        return self.create_model(provider="groq", model_id=model_id, **kwargs)

    def openai_chat(self, model_id: Optional[str] = None, **kwargs: Any) -> OpenAIChat:
        """
        Creates an OpenAIChat model instance.

        Args:
            model_id (Optional[str]): Optional model id. Default is None.
            **kwargs: Additional parameters passed to the OpenAIChat constructor.

        Returns:
                OpenAIChat: An instance of the OpenAIChat model.
        """
        return self.create_model(
            provider="openai",
            model_id=model_id,
            openai_variant="chat",
            **kwargs,
        )

    def openai_responses(self, model_id: Optional[str] = None, **kwargs: Any) -> OpenAIResponses:
        """
        Creates an OpenAIResponses model instance.

        Args:
            model_id (Optional[str]): Optional model id. Default is None.
            **kwargs: Additional parameters passed to the OpenAIResponses constructor.

        Returns:
                OpenAIResponses: An instance of the OpenAIResponses model.
        """
        return self.create_model(
            provider="openai",
            model_id=model_id,
            openai_variant="responses",
            **kwargs,
        )

    def open_responses(self, model_id: Optional[str] = None, **kwargs: Any) -> OpenResponses:
        """
        Creates an OpenResponses model instance.

        Args:
            model_id (Optional[str]): Optional model id. Default is None.
            **kwargs: Additional parameters passed to the OpenResponses constructor.

        Returns:
                OpenResponses: An instance of the OpenResponses model.
        """
        return self.create_model(
            provider="openai",
            model_id=model_id,
            openai_variant="open_responses",
            **kwargs,
        )

    def openai_like(self, model_id: Optional[str] = None, **kwargs: Any) -> OpenAILike:
        """
        Creates an OpenAILike model instance.

        Args:
            model_id (Optional[str]): Optional model id. Default is None.
            **kwargs: Additional parameters passed to the OpenAILike constructor.

        Returns:
                OpenAILike: An instance of the OpenAILike model.
        """
        return self.create_model(
            provider="openai",
            model_id=model_id,
            openai_variant="like",
            **kwargs,
        )

    def _resolve_factory_key(self, provider: str, openai_variant: str = "chat") -> str:
        """
        Resolves the internal factory key used to retrieve the model constructor based on provider and OpenAI variant.

        Args:
            provider (str): The model provider name.
            openai_variant (str): The OpenAI variant name. Default is "chat".

        Returns:
                str: The factory key corresponding to the model constructor.

        Raises:
                ValueError: If the provider or OpenAI variant is unsupported.
        """
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
        """
        Retrieves the list of constructor parameter names for the specified factory key.

        Args:
            factory_key (str): The factory key identifying the model constructor.

        Returns:
                List[str]: List of constructor parameter names, excluding 'self'.
        """
        constructor = self._MODEL_FACTORIES[factory_key]
        signature = inspect.signature(constructor.__init__)
        return [name for name in signature.parameters if name != "self"]

    def _validate_kwargs(self, factory_key: str, kwargs: Dict[str, Any]) -> None:
        """
        Validates that all provided kwargs are valid constructor parameters for the specified factory.

        Args:
            factory_key (str): The factory key identifying the model constructor.
            kwargs (Dict[str, Any]): The kwargs to validate.

        Raises:
            ValueError: If any invalid parameters are found in kwargs.
        """
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
    agent.print_response("Hello!")
```