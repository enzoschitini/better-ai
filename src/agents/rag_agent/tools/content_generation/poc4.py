from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Tuple

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from pydantic import BaseModel, Field

from src.vector_store.pinecone.client import PineconeClient
from src.vector_store.pinecone.retriever import PineconeRetriever
from src.vector_store.pinecone.utils.retrieval_manager import RetrievalManager

DEFAULT_MODEL = "gpt-4.1-mini"


class GeneratedContentParse(BaseModel):
    title: str = Field(..., description="Main title for the generated content")
    summary: str = Field(..., description="Short summary with 1-2 sentences")
    body: str = Field(..., description="Main content text")
    cta: str = Field(..., description="Call to action")
    hashtags: List[str] = Field(
        ..., description="Relevant social hashtags, each item must start with #"
    )
    sources_used: List[str] = Field(
        ..., description="List of key source snippets or documents used"
    )


class ContentBatchOutput(BaseModel):
    query: str
    objective: str
    content_count: int
    items: List[GeneratedContentParse]


class GenerateContent:
    """Encapsulates only the logic required to generate structured content."""

    def __init__(self, model_id: str = DEFAULT_MODEL, filter_search: Optional[dict] = None) -> None:
        self.model_id = model_id
        self.filter_search = filter_search or {}

    def _validate_body_range(self, body_min_chars: int, body_max_chars: int) -> None:
        if body_min_chars < 1:
            raise ValueError("body_min_chars must be greater than or equal to 1")
        if body_max_chars < body_min_chars:
            raise ValueError("body_max_chars must be greater than or equal to body_min_chars")


    def _is_body_within_range(self, content: GeneratedContentParse, body_min_chars: int, body_max_chars: int) -> bool:
        body_size = len(content.body)
        return body_min_chars <= body_size <= body_max_chars

    def _build_content_creator_agent(self) -> Agent:
        return Agent(
            model=OpenAIChat(id=self.model_id),
            output_schema=GeneratedContentParse,
            markdown=True,
            instructions=[
                "You are a content creation specialist.",
                "Always use only the provided context as the primary source.",
                "If context is insufficient, state what is missing instead of inventing facts.",
                "Return polished, coherent, publication-ready content.",
                "The output must strictly follow the requested structured fields.",
                "Generate relevant hashtags aligned with the topic and objective.",
            ],
            description="Generates content using retrieval context as input.",
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
        creator_agent = self._build_content_creator_agent()

        variation_angles = [
            "benefit-driven narrative",
            "practical educational approach",
            "premium positioning perspective",
            "problem-solution framing",
            "light comparative framing",
        ]
        variation_openings = [
            "Start with a concise insight statement.",
            "Start with a short practical scenario.",
            "Start with a premium brand-oriented hook.",
            "Start with a common pain point.",
            "Start with a contrast between options.",
        ]
        variation_rhythms = [
            "Use medium paragraphs.",
            "Use shorter paragraphs and faster pacing.",
            "Use a more refined and descriptive pacing.",
            "Use direct and objective pacing.",
            "Use balanced pacing with one concise list if useful.",
        ]

        variation_angle = variation_angles[index % len(variation_angles)]
        variation_opening = variation_openings[index % len(variation_openings)]
        variation_rhythm = variation_rhythms[index % len(variation_rhythms)]

        prompt_base = f"""
Objective:
{objective}

User query for retrieval:
{query}

Retrieved context:
{context}

Additional requirements:
{extra_requirements or "None"}

Variant:
{index + 1} of {content_count}

Instructions:
- Build the final content grounded in the retrieved context.
- Keep a clear structure and avoid unsupported facts.
- Make this variant distinct in angle and wording from the others.
- Preferred angle for this variant: {variation_angle}.
- Opening guidance: {variation_opening}
- Writing rhythm guidance: {variation_rhythm}
- The body field must have between {body_min_chars} and {body_max_chars} characters.
- Include 5 to 10 relevant hashtags in the hashtags field.
""".strip()

        attempt = 0
        max_attempts = 3
        generated_content: Optional[GeneratedContentParse] = None

        while attempt < max_attempts:
            attempt += 1
            prompt = prompt_base

            if attempt > 1 and generated_content is not None:
                prompt = f"""
{prompt_base}

Correction:
- Previous body length was {len(generated_content.body)} characters.
- Regenerate and strictly keep body length between {body_min_chars} and {body_max_chars}.
""".strip()

            response = creator_agent.run(prompt)
            generated_content = response.content

            if self._is_body_within_range(
                content=generated_content,
                body_min_chars=body_min_chars,
                body_max_chars=body_max_chars,
            ):
                break

        if generated_content is None:
            raise RuntimeError("Failed to generate structured content")

        return index, generated_content


    def retrieve_context(
        self,
        query: str,
        filter_search: dict,
        max_results: int = 5,
    ) -> str:
        """
        Retrieves context from the vector store to be used as input for content creation.
        """
        try:

            pine_client = PineconeClient(
                index_name="backai-vectorstore",
                main_namespace="knowledge_base_content_agent_oboticario"
            )
            retriver = PineconeRetriever(pine_client)

            documents = retriver.similarity_search(
                query=query,
                k=max_results,
                filter_search=filter_search
            )

            manager = RetrievalManager(docs=documents)
            context = manager.generate_context()

            return context
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve context: {str(e)}") from e

    def generate(
        self,
        query: str,
        objective: str,
        filter_search: Optional[dict] = None,
        max_results: int = 5,
        content_count: int = 1,
        body_min_chars: int = 700,
        body_max_chars: int = 1200,
        extra_requirements: Optional[str] = None,
    ) -> ContentBatchOutput:
        if content_count < 1:
            raise ValueError("content_count must be greater than or equal to 1")

        self._validate_body_range(body_min_chars=body_min_chars, body_max_chars=body_max_chars)

        effective_filter_search = filter_search if filter_search is not None else self.filter_search
        resolved_context = self.retrieve_context(
            query=query,
            filter_search=effective_filter_search,
                max_results=max_results,
            )

        generated_map: dict[int, GeneratedContentParse] = {}
        max_workers = min(content_count, 5)

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

        return ContentBatchOutput(
            query=query,
            objective=objective,
            content_count=content_count,
            items=generated_items,
        )




if __name__ == "__main__":
    import time
    from src.agents.rag_agent.tools.content_generation.example_requests import EXAMPLE_REQUESTS
    from src.agents.rag_agent.tools.content_generation.markdown_utils import save_posts_markdown

    payload = EXAMPLE_REQUESTS["example_6"]

    def generate_content(
        query: str,
        objective: str,
        filter_search: dict,
        content_count: int = 1,
        body_min_chars: int = 700,
        body_max_chars: int = 1200,
        max_results: int = 5,
        model_id: str = DEFAULT_MODEL,
        extra_requirements: Optional[str] = None,
    ) -> ContentBatchOutput:
        """
        Two-step pipeline:
        1) Retrieve context using the retriever.
        2) Use the retrieved context as direct input for the content creator agent.
        3) Generate one or more structured content variants.
        """
        try:
            start_time = time.time()
            generator = GenerateContent(model_id=model_id, filter_search=filter_search)
            generated_content = generator.generate(
                query=query,
                objective=objective,
                max_results=max_results,
                content_count=content_count,
                body_min_chars=body_min_chars,
                body_max_chars=body_max_chars,
                extra_requirements=extra_requirements,
            )

            end_time = time.time()
            elapsed_time = end_time - start_time

            markdown_file = save_posts_markdown(
                posts_payload=generated_content,
                output_file="src/agents/rag_agent/tools/content_generation",
                document_title="Marketing Posts",
            )

            print(f"\nMarkdown file generated at: {markdown_file}")
            print(f"\nElapsed time: {elapsed_time:.2f} seconds")

        except Exception as e:
            raise RuntimeError(f"Failed to generate content using retrieval context: {str(e)}") from e


    def test_retrieval():
        query = "Mate Salicylic"
        filter_search = payload.get("filter_search", {})
        max_results = payload.get("max_results", 5)

        generator = GenerateContent()
        context = generator.retrieve_context(
            query=query,
            filter_search=filter_search,
            max_results=max_results,
        )
    
    generate_content(**payload)
    #test_retrieval()


# python -m src.agents.rag_agent.tools.content_generation.poc4