from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Tuple

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from src.tracing.logging_config import LogManager
from src.vector_store.pinecone.client import PineconeClient
from src.vector_store.pinecone.retriever import PineconeRetriever
from src.vector_store.pinecone.utils.retrieval_manager import RetrievalManager

from src.agents.content_agent.tools.content_generation.config import (
    GeneratedContentParse,
    ContentBatchOutput,
    AGENT_DESCRIPTION,
    AGENT_INSTRUCTIONS,
    DEFAULT_BODY_MAX_CHARS,
    DEFAULT_BODY_MIN_CHARS,
    DEFAULT_CONTENT_COUNT,
    DEFAULT_MAX_RESULTS,
    DEFAULT_MODEL,
    PINECONE_INDEX_NAME,
    PINECONE_MAIN_NAMESPACE,
    PROMPT_BASE_TEMPLATE,
    PROMPT_CORRECTION_TEMPLATE,
    VARIATION_ANGLES,
    VARIATION_OPENINGS,
    VARIATION_RHYTHMS,
)

class GenerateContent:
    """
    Generates structured content variants using retrieval context and controlled prompt strategies.
    This class centralizes agent construction, context retrieval, and multi-variant generation with validation.

    Args:
    :param model_id (str): Model identifier used to initialize the chat model. Default is "gpt-4.1-mini"
    :param filter_search (Optional[dict]): Default retrieval filter used when no runtime filter is provided. Default is None

    Methods:
            retrieve_context(): Retrieves textual context from Pinecone using the provided query and filters.
            generate(): Generates one or more structured content variants from retrieved context.
    """

    def __init__(self, model_id: str = DEFAULT_MODEL, filter_search: Optional[dict] = None, logging_level: str = "INFO") -> None:
        LogManager.setup(
            fmt="%(asctime)s | %(levelname)-8s | %(message)s | %(name)s",
            level=logging_level
        )

        self.logger = LogManager.get_logger(f"{type(self).__module__}.{type(self).__name__}")
        
        self.model_id = model_id
        self.filter_search = filter_search or {}
        self.logger.debug(
            "GenerateContent initialized with model_id=%s and default_filter_keys=%s",
            self.model_id,
            sorted(list(self.filter_search.keys())),
        )

    def _validate_body_range(self, body_min_chars: int, body_max_chars: int) -> None:
        """
        Validates the allowed character range for the generated body text.
        It ensures the minimum is positive and the maximum is not smaller than the minimum.

        Args:
        body_min_chars (int): Minimum number of characters allowed for the body.
        body_max_chars (int): Maximum number of characters allowed for the body.

        Raises:
                ValueError: Raised when min or max limits are invalid.
        """
        self.logger.debug(
            "Validating body range: min=%d, max=%d",
            body_min_chars,
            body_max_chars,
        )
        if body_min_chars < 1:
            raise ValueError("body_min_chars must be greater than or equal to 1")
        if body_max_chars < body_min_chars:
            raise ValueError("body_max_chars must be greater than or equal to body_min_chars")


    def _is_body_within_range(self, content: GeneratedContentParse, body_min_chars: int, body_max_chars: int) -> bool:
        """
        Checks whether the generated body length is within the configured limits.
        This helper is used to decide if a generated attempt can be accepted.

        Args:
        content (GeneratedContentParse): Generated content object containing the body text.
        body_min_chars (int): Minimum number of characters allowed for the body.
        body_max_chars (int): Maximum number of characters allowed for the body.

        Returns:
                bool: True when body length is within range, otherwise False.
        """
        body_size = len(content.body)
        return body_min_chars <= body_size <= body_max_chars

    def _build_content_creator_agent(self) -> Agent:
        """
        Builds and returns the content creator agent configured for structured output.
        The returned agent is ready to generate content based on retrieval context.

        Returns:
                Agent: Configured agent instance for content generation.
        """
        self.logger.debug("Building content creator agent with model_id=%s", self.model_id)
        return Agent(
            model=OpenAIChat(id=self.model_id),
            output_schema=GeneratedContentParse,
            markdown=True,
            instructions=AGENT_INSTRUCTIONS,
            description=AGENT_DESCRIPTION,
        )

    def _generate_single_variant(
        self,
        index: int,
        content_count: int,
        query: str,
        objective: str,
        context: str,
        body_min_chars: int,
        body_max_chars: int,
        extra_requirements: Optional[str],
    ) -> Tuple[int, GeneratedContentParse]:
        """
        Generates a single content variant using style guidance and retry logic.
        It retries generation when body length is out of range and returns the indexed result.

        Args:
        index (int): Zero-based position of the variant in the batch.
        content_count (int): Total number of variants requested in the batch.
        query (str): Retrieval query that contextualizes generation.
        objective (str): Business or communication objective for the generated content.
        context (str): Retrieved context used as factual grounding.
        body_min_chars (int): Minimum body size in characters.
        body_max_chars (int): Maximum body size in characters.
        extra_requirements (Optional[str]): Additional generation constraints.

        Returns:
            Tuple[int, GeneratedContentParse]: Variant index and generated structured content.

        Raises:
            RuntimeError: Raised when structured content cannot be generated.
        """
        try:
            self.logger.debug(
                "Generating variant %d/%d with body range min=%d max=%d",
                index + 1,
                content_count,
                body_min_chars,
                body_max_chars,
            )
            creator_agent = self._build_content_creator_agent()

            variation_angle = VARIATION_ANGLES[index % len(VARIATION_ANGLES)]
            variation_opening = VARIATION_OPENINGS[index % len(VARIATION_OPENINGS)]
            variation_rhythm = VARIATION_RHYTHMS[index % len(VARIATION_RHYTHMS)]

            prompt_base = PROMPT_BASE_TEMPLATE.format(
                objective=objective,
                query=query,
                context=context,
                extra_requirements=extra_requirements or "None",
                variant_number=index + 1,
                content_count=content_count,
                variation_angle=variation_angle,
                variation_opening=variation_opening,
                variation_rhythm=variation_rhythm,
                body_min_chars=body_min_chars,
                body_max_chars=body_max_chars,
            )

            attempt = 0
            max_attempts = 3
            generated_content: Optional[GeneratedContentParse] = None

            while attempt < max_attempts:
                attempt += 1
                self.logger.debug(
                    "Variant %d attempt %d/%d",
                    index + 1,
                    attempt,
                    max_attempts,
                )
                prompt = prompt_base

                if attempt > 1 and generated_content is not None:
                    prompt = PROMPT_CORRECTION_TEMPLATE.format(
                        prompt_base=prompt_base,
                        previous_body_length=len(generated_content.body),
                        body_min_chars=body_min_chars,
                        body_max_chars=body_max_chars,
                    )

                response = creator_agent.run(prompt)
                generated_content = response.content

                if self._is_body_within_range(
                    content=generated_content,
                    body_min_chars=body_min_chars,
                    body_max_chars=body_max_chars,
                ):
                    self.logger.debug(
                        "Variant %d accepted with body_length=%d",
                        index + 1,
                        len(generated_content.body),
                    )
                    break

                self.logger.warning(
                    "Variant %d out of range with body_length=%d (expected %d-%d). Retrying.",
                    index + 1,
                    len(generated_content.body),
                    body_min_chars,
                    body_max_chars,
                )

            if generated_content is None:
                raise RuntimeError("Failed to generate structured content")

            self.logger.info("Variant %d generated successfully", index + 1)
            return index, generated_content
        
        except Exception as e:
            self.logger.exception("Variant %d generation failed", index + 1)
            raise RuntimeError(f"Failed to generate variant {index + 1}: {str(e)}") from e


    def retrieve_context(
        self,
        query: str,
        filter_search: dict,
        max_results: int = DEFAULT_MAX_RESULTS,
    ) -> str:
        """
        Retrieves context from the vector store based on query and filtering constraints.
        It performs similarity search and consolidates the result into a single context string.

        Args:
        query (str): Search query used in vector similarity retrieval.
        filter_search (dict): Filter payload applied to constrain retrieval scope.
        max_results (int): Maximum number of retrieved documents. Default is "5"

        Returns:
            dict: A dictionary containing the consolidated context string and the list of relevant documents.

        Raises:
            RuntimeError: Raised when context retrieval fails.
        """
        try:
            self.logger.info("Retrieving context with max_results=%d", max_results)
            self.logger.debug("Context retrieval query=%s", query)
            self.logger.debug("Context retrieval filter keys=%s", sorted(list(filter_search.keys())))

            pine_client = PineconeClient(
                index_name=PINECONE_INDEX_NAME,
                main_namespace=PINECONE_MAIN_NAMESPACE,
            )
            retriver = PineconeRetriever(pine_client)

            documents = retriver.similarity_search(
                query=query,
                k=max_results,
                filter_search=filter_search
            )

            manager = RetrievalManager(docs=documents)
            context = manager.generate_context()
            relevant_docs = manager.get_files()

            self.logger.info("Context retrieval completed with %d documents", len(documents))

            return {
                "context": context,
                "relevant_docs": relevant_docs,
            }
        except Exception as e:
            self.logger.exception("Context retrieval failed")
            raise RuntimeError(f"Failed to retrieve context: {str(e)}") from e

    def generate(
        self,
        query: str,
        objective: str,
        filter_search: Optional[dict] = None,
        max_results: int = DEFAULT_MAX_RESULTS,
        content_count: int = DEFAULT_CONTENT_COUNT,
        body_min_chars: int = DEFAULT_BODY_MIN_CHARS,
        body_max_chars: int = DEFAULT_BODY_MAX_CHARS,
        extra_requirements: Optional[str] = None,
    ) -> ContentBatchOutput:
        """
        Generates a full batch of structured content variants from retrieved context.
        It validates body limits, retrieves context, runs variant generation concurrently, and returns ordered results.

        Args:
        query (str): Retrieval query that anchors generated content.
        objective (str): Objective that guides tone and structure of generated text.
        filter_search (Optional[dict]): Retrieval filter override for this execution. Default is None
        max_results (int): Maximum number of documents to retrieve. Default is "5"
        content_count (int): Number of content variants to generate. Default is "1"
        body_min_chars (int): Minimum body length in characters. Default is "700"
        body_max_chars (int): Maximum body length in characters. Default is "1200"
        extra_requirements (Optional[str]): Extra requirements appended to the generation prompt. Default is None

        Returns:
            ContentBatchOutput: Structured batch output containing generated items.

        Raises:
            ValueError: Raised when requested content count is invalid.
        """
        try:
            self.logger.info(
                "Starting content generation for query=%s with content_count=%d",
                query,
                content_count,
            )
            if content_count < 1:
                raise ValueError("content_count must be greater than or equal to 1")

            self._validate_body_range(body_min_chars=body_min_chars, body_max_chars=body_max_chars)

            effective_filter_search = filter_search if filter_search is not None else self.filter_search
            result = self.retrieve_context(
                query=query,
                filter_search=effective_filter_search,
                    max_results=max_results,
                )
            
            resolved_context = result["context"]
            relevant_docs = result["relevant_docs"]

            self.logger.info(f"Retrieved context of length {len(resolved_context)} with {len(relevant_docs)} relevant documents")

            generated_map: dict[int, GeneratedContentParse] = {}
            max_workers = min(content_count, 5)
            self.logger.debug("Generating variants with max_workers=%d", max_workers)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(
                        self._generate_single_variant,
                        index,
                        content_count,
                        query,
                        objective,
                        resolved_context,
                        body_min_chars,
                        body_max_chars,
                        extra_requirements,
                    )
                    for index in range(content_count)
                ]

                for future in as_completed(futures):
                    variant_index, generated_content = future.result()
                    generated_map[variant_index] = generated_content

            generated_items = [generated_map[index] for index in range(content_count)]
            self.logger.info("Content generation completed with %d items", len(generated_items))

            return ContentBatchOutput(
                query=query,
                objective=objective,
                content_count=content_count,
                items=generated_items,
                relevant_docs=relevant_docs,
            )
        
        except Exception as e:
            self.logger.exception("Content generation failed")
            raise RuntimeError(f"Failed to generate content: {str(e)}") from e
