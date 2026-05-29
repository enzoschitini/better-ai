import json
from pathlib import Path
from typing import Any, List, Optional, Union
import uuid

from pydantic import BaseModel


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
        output_path = Path(output_dir) / "retrieval_context.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown_content, encoding="utf-8")
        return str(output_path)
    except Exception as e:
        raise RuntimeError(f"Failed to save context markdown: {str(e)}") from e


def _normalize_posts_payload(posts_payload: Union[BaseModel, dict, str]) -> dict:
    if isinstance(posts_payload, str):
        return json.loads(posts_payload)
    if isinstance(posts_payload, dict):
        return posts_payload
    if isinstance(posts_payload, BaseModel):
        return posts_payload.model_dump()
    raise ValueError("posts_payload must be a Pydantic model, dict, or JSON string")


def format_posts_json_to_markdown(
    posts_payload: Union[BaseModel, dict, str],
    document_title: str = "Generated Content Batch",
) -> str:
    """
    Converts generated posts payload into a Markdown document string.
    """
    try:
        payload = _normalize_posts_payload(posts_payload=posts_payload)

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
                    body,
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
    posts_payload: Union[BaseModel, dict, str],
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
