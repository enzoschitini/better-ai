


if __name__ == "__main__":
    import time
    from typing import Optional

    from src.agents.rag_agent.tools.content_generation.module import GenerateContent, ContentBatchOutput
    from src.agents.rag_agent.tools.content_generation.config import (
        DEFAULT_CONTENT_COUNT, DEFAULT_BODY_MIN_CHARS, DEFAULT_BODY_MAX_CHARS, DEFAULT_MAX_RESULTS, DEFAULT_MODEL
    )

    from src.agents.rag_agent.tools.content_generation.test.example_requests import EXAMPLE_REQUESTS
    from src.agents.rag_agent.tools.content_generation.markdown_utils import save_posts_markdown

    payload = EXAMPLE_REQUESTS["example_4"]

    def generate_content(
        query: str,
        objective: str,
        filter_search: dict,
        content_count: int = DEFAULT_CONTENT_COUNT,
        body_min_chars: int = DEFAULT_BODY_MIN_CHARS,
        body_max_chars: int = DEFAULT_BODY_MAX_CHARS,
        max_results: int = DEFAULT_MAX_RESULTS,
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
        result = generator.retrieve_context(
            query=query,
            filter_search=filter_search,
            max_results=max_results,
        )

        print(f"Retrieved Context:\n{result['context']}")
        print(f"Relevant Documents:\n{result['relevant_docs']}")
    
    generate_content(**payload)
    #test_retrieval()

# python -m src.agents.rag_agent.tools.content_generation.test.content_generator