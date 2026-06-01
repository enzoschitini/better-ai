from typing import List, Optional

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from pydantic import BaseModel, Field

from src.agents.rag_agent.tools.toolkit import RetrievalAugmentedGeneration


DEFAULT_MODEL = "gpt-4.1-mini"


class GeneratedContent(BaseModel):
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
    items: List[GeneratedContent]


def _validate_body_range(body_min_chars: int, body_max_chars: int) -> None:
    if body_min_chars < 1:
        raise ValueError("body_min_chars must be greater than or equal to 1")
    if body_max_chars < body_min_chars:
        raise ValueError("body_max_chars must be greater than or equal to body_min_chars")


def _is_body_within_range(content: GeneratedContent, body_min_chars: int, body_max_chars: int) -> bool:
    body_size = len(content.body)
    return body_min_chars <= body_size <= body_max_chars


def retrieve_context(
    query: str,
    filter_search: dict,
    max_results: int = 5,
) -> str:
    """
    Retrieves context from the vector store to be used as input for content creation.
    """
    try:
        rag_tool = RetrievalAugmentedGeneration(filter_search=filter_search)
        return rag_tool.get_relevant_documents(query=query, max_results=max_results)
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve context: {str(e)}") from e


def build_content_creator_agent(model_id: str = DEFAULT_MODEL) -> Agent:
    """
    Agent specialized in generating content using an explicit external context.
    """
    return Agent(
        model=OpenAIChat(id=model_id),
        output_schema=GeneratedContent,
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


def generate_content_with_retrieval(
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
        if content_count < 1:
            raise ValueError("content_count must be greater than or equal to 1")

        _validate_body_range(body_min_chars=body_min_chars, body_max_chars=body_max_chars)

        context = retrieve_context(
            query=query,
            filter_search=filter_search,
            max_results=max_results,
        )

        creator_agent = build_content_creator_agent(model_id=model_id)

        generated_items: List[GeneratedContent] = []

        for index in range(content_count):
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
- The body field must have between {body_min_chars} and {body_max_chars} characters.
- Include 5 to 10 relevant hashtags in the hashtags field.
""".strip()

            attempt = 0
            max_attempts = 3
            generated_content: Optional[GeneratedContent] = None

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

                if _is_body_within_range(
                    content=generated_content,
                    body_min_chars=body_min_chars,
                    body_max_chars=body_max_chars,
                ):
                    break

            if generated_content is None:
                raise RuntimeError("Failed to generate structured content")

            generated_items.append(generated_content)

        return ContentBatchOutput(
            query=query,
            objective=objective,
            content_count=content_count,
            items=generated_items,
        )
    except Exception as e:
        raise RuntimeError(f"Failed to generate content using retrieval context: {str(e)}") from e


if __name__ == "__main__":
    import time
    start_time = time.time()

    generated_content = generate_content_with_retrieval(
        query="Malbec e posicionamento de marca",
        objective="Criar um artigo curto de marketing para blog sobre a linha Malbec.",
        filter_search={"collection_id": ["oboticario"]},
        content_count=2,
        body_min_chars=700,
        body_max_chars=1200,
        max_results=5,
        extra_requirements="Tom premium, linguagem persuasiva e CTA no final.",
    )

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(generated_content.model_dump_json(indent=2))
    print(f"\nElapsed time: {elapsed_time:.2f} seconds")


# python -m src.agents.rag_agent.tools.content_generation.poc1