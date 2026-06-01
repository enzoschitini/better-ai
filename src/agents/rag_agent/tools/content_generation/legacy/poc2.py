from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
from typing import List, Optional, Tuple, Union
import uuid

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.anthropic import Claude
from pydantic import BaseModel, Field

from src.vector_store.pinecone.client import PineconeClient
from src.vector_store.pinecone.retriever import PineconeRetriever
from src.vector_store.pinecone.utils.retrieval_manager import RetrievalManager
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


def format_context_to_markdown(context: str, source_files: Optional[List[str]] = None) -> str:
    """
    Builds a markdown document with retrieval context and source files.
    """
    try:
        lines: List[str] = [
            "# Retrieval Context",
            "",
            "## Source Files",
            "",
        ]

        if source_files:
            lines.extend([f"- {source_file}" for source_file in source_files])
        else:
            lines.append("- No source files found")

        lines.extend(
            [
                "",
                "## Context",
                "",
                context if context else "No context retrieved.",
                "",
            ]
        )

        return "\n".join(lines)
    except Exception as e:
        raise RuntimeError(f"Failed to format context markdown: {str(e)}") from e


def save_context_markdown(
    context: str,
    source_files: Optional[List[str]] = None,
    output_dir: str = "src/agents/rag_agent/tools/content_generation",
) -> str:
    """
    Saves retrieval context and source files into a markdown file.
    """
    try:
        markdown_content = format_context_to_markdown(context=context, source_files=source_files)
        output_path = Path(output_dir) / f"retrieval_context.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown_content, encoding="utf-8")
        return str(output_path)
    except Exception as e:
        raise RuntimeError(f"Failed to save context markdown: {str(e)}") from e


def format_posts_json_to_markdown(
    posts_payload: Union[ContentBatchOutput, dict, str],
    document_title: str = "Generated Content Batch",
) -> str:
    """
    Converts generated posts payload into a Markdown document string.
    """
    try:
        if isinstance(posts_payload, ContentBatchOutput):
            payload = posts_payload.model_dump()
        elif isinstance(posts_payload, str):
            payload = json.loads(posts_payload)
        elif isinstance(posts_payload, dict):
            payload = posts_payload
        else:
            raise ValueError("posts_payload must be ContentBatchOutput, dict, or JSON string")

        query = payload.get("query", "")
        objective = payload.get("objective", "")
        content_count = payload.get("content_count", 0)
        items = payload.get("items", [])

        lines: List[str] = [
            f"# {document_title}",
            "",
            "## Batch Metadata",
            "",
            f"- Query: {query}",
            f"- Objective: {objective}",
            f"- Content count: {content_count}",
            "",
            "## Posts",
            "",
        ]

        for index, item in enumerate(items, start=1):
            title = item.get("title", "")
            summary = item.get("summary", "")
            body = item.get("body", "")
            cta = item.get("cta", "")
            hashtags = item.get("hashtags", [])
            sources_used = item.get("sources_used", [])

            lines.extend(
                [
                    f"## {index}: {title}",
                    "",
                    "#### Summary",
                    "",
                    f"### {summary}",
                    "",
                    "#### Body",
                    "",
                    f"### {body}",
                    "",
                    "#### Call to Action",
                    "",
                    f"### {cta}",
                    "",
                    "#### Hashtags",
                    "",
                    " ".join(hashtags),
                    "",
                    "#### Sources Used",
                    "",
                ]
            )

            if sources_used:
                lines.extend([f"- {source}" for source in sources_used])
            else:
                lines.append("- No sources provided")

            lines.append("")

        return "\n".join(lines).strip() + "\n"
    except Exception as e:
        raise RuntimeError(f"Failed to format posts JSON to markdown: {str(e)}") from e


def save_posts_markdown(
    posts_payload: Union[ContentBatchOutput, dict, str],
    output_file: Optional[str] = None,
    document_title: str = "Generated Content Batch",
) -> str:
    """
    Formats generated posts and saves them into a .md file.
    """
    try:
        markdown_content = format_posts_json_to_markdown(
            posts_payload=posts_payload,
            document_title=document_title,
        )

        unique_id = uuid.uuid4().hex[:8]

        if not output_file:
            output_path = Path(f"generated_posts_{unique_id}.md")
        else:
            candidate_path = Path(output_file)

            if candidate_path.exists() and candidate_path.is_dir():
                output_path = candidate_path / f"{unique_id}.md"
            elif candidate_path.suffix.lower() != ".md":
                output_path = candidate_path / f"{unique_id}.md"
            else:
                output_path = candidate_path

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown_content, encoding="utf-8")

        return str(output_path)
    except Exception as e:
        raise RuntimeError(f"Failed to save posts markdown: {str(e)}") from e


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
        source_files = manager.get_files()

        context_markdown_path = save_context_markdown(
            context=context,
            source_files=source_files,
        )
        print(f"Context markdown saved at: {context_markdown_path}")

        #rag_tool = RetrievalAugmentedGeneration(filter_search=filter_search)
        #rag_tool.get_relevant_documents(query=query, max_results=max_results)
        return context
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve context: {str(e)}") from e


def build_content_creator_agent(model_id: str = DEFAULT_MODEL) -> Agent:
    """
    Agent specialized in generating content using an explicit external context.
    """
    return Agent(
        #model=OpenAIChat(id=model_id),
        model=Claude(id="claude-opus-4-1-20250805"),
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


def _generate_single_variant(
    index: int,
    content_count: int,
    query: str,
    objective: str,
    context: str,
    body_min_chars: int,
    body_max_chars: int,
    model_id: str,
    extra_requirements: Optional[str],
) -> Tuple[int, GeneratedContent]:
    creator_agent = build_content_creator_agent(model_id=model_id)

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

    return index, generated_content


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

        generated_map: dict[int, GeneratedContent] = {}
        max_workers = min(content_count, 5)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(
                    _generate_single_variant,
                    index,
                    content_count,
                    query,
                    objective,
                    context,
                    body_min_chars,
                    body_max_chars,
                    model_id,
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
    except Exception as e:
        raise RuntimeError(f"Failed to generate content using retrieval context: {str(e)}") from e


if __name__ == "__main__":
    import time
    from agents.rag_agent.tools.content_generation.test.example_requests import EXAMPLE_REQUESTS

    payload = EXAMPLE_REQUESTS["example_4"]

    def generate_content():
        start_time = time.time()

        generated_content = generate_content_with_retrieval(**payload)

        end_time = time.time()
        elapsed_time = end_time - start_time

        #print(generated_content.model_dump_json(indent=2))

        markdown_file = save_posts_markdown(
            posts_payload=generated_content,
            output_file="src/agents/rag_agent/tools/content_generation",
            document_title="Marketing Posts",
        )

        print(f"\nMarkdown file generated at: {markdown_file}")
        print(f"\nElapsed time: {elapsed_time:.2f} seconds")
    
    def test_retrieval():
        query = "Mate Salicylic"
        filter_search = payload.get("filter_search", {})
        max_results = payload.get("max_results", 5)

        context = retrieve_context(
            query=query,
            filter_search=filter_search,
            max_results=max_results,
        )
    
    #generate_content()
    test_retrieval()


# python -m src.agents.rag_agent.tools.content_generation.poc2