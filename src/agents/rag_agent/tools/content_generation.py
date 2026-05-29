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

        context = retrieve_context(
            query=query,
            filter_search=filter_search,
            max_results=max_results,
        )

        creator_agent = build_content_creator_agent(model_id=model_id)

        generated_items: List[GeneratedContent] = []

        for index in range(content_count):
            prompt = f"""
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
- Include 5 to 10 relevant hashtags in the hashtags field.
""".strip()

            response = creator_agent.run(prompt)
            generated_items.append(response.content)

        return ContentBatchOutput(
            query=query,
            objective=objective,
            content_count=content_count,
            items=generated_items,
        )
    except Exception as e:
        raise RuntimeError(f"Failed to generate content using retrieval context: {str(e)}") from e


if __name__ == "__main__":
    generated_content = generate_content_with_retrieval(
        query="Malbec e posicionamento de marca",
        objective="Criar um artigo curto de marketing para blog sobre a linha Malbec.",
        filter_search={"collection_id": ["oboticario"]},
        content_count=2,
        max_results=5,
        extra_requirements="Tom premium, linguagem persuasiva e CTA no final.",
    )

    print(generated_content.model_dump_json(indent=2))


# python -m src.agents.rag_agent.tools.content_generation