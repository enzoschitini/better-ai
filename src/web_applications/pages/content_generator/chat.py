import json
import time

from typing import Any, Callable, Dict, List, Tuple

import streamlit as st
import streamlit.components.v1 as components

from src.web_applications.pages.content_generator.generate_content_tools import GenerateContentTools


class Chat:
    """
    Encapsulate the content-generator chat workflow for Streamlit.

    This class coordinates the full lifecycle of a chat interaction:
    collecting user input, invoking content generation tools, storing
    conversation artifacts in ``st.session_state``, rendering generated
    posts, and scrolling to the latest result.

    Dependencies such as configuration resolution and markdown rendering
    are injected to keep responsibilities separated and improve testability.
    """

    def __init__(
        self,
        get_config: Callable[[], Dict[str, Any]],
        markdown_tools: Any,
        fake_content: bool = False,
        fake_content_path: str = "src/web_applications/applications/post.json",
    ) -> None:
        """
        Initialize chat dependencies and optional fake-content mode.

        Args:
            get_config: Callable that returns the current runtime configuration
                used to initialize ``GenerateContentTools``.
            markdown_tools: Helper object responsible for markdown generation
                and copy-button rendering for each generated post.
            fake_content: If ``True``, bypasses real generation and loads
                content from ``fake_content_path``.
            fake_content_path: Path to the JSON file used in fake-content mode.

        Returns:
            None.
        """
        self.get_config = get_config
        self.markdown_tools = markdown_tools
        self.fake_content = fake_content
        self.fake_content_path = fake_content_path

    def chat(self) -> None:
        """
        Execute one complete chat cycle in the UI.

        Flow:
            1. Read user prompt from Streamlit chat input.
            2. Build generation tools from current config.
            3. Generate or load content when a prompt is provided.
            4. Persist generated item in session state.
            5. Render all generated items and apply auto-scroll.

        Returns:
            None.

        Error Messages:
            - "An error occurred during the chat process: {str(e)}"
        """
        try:
            prompt = self._get_prompt()
            generate_content_tools = self._build_generate_tools()
            should_scroll_to_last_content = False

            if prompt:
                generated_item = self._generate_or_load_content(prompt, generate_content_tools)
                if generated_item is None:
                    return

                self._append_generated_content(generated_item)
                should_scroll_to_last_content = True

            self._render_generated_contents()
            self._scroll_to_last_content_if_needed(should_scroll_to_last_content)

        except Exception as e:
            st.error(f"An error occurred during the chat process: {str(e)}")

    def _get_prompt(self) -> str:
        """
        Read the user input from the Streamlit chat input component.

        Returns:
            The prompt string entered by the user. If no message was
            submitted in the current rerun, Streamlit may return a falsy value.
        """
        return st.chat_input("Digite algo para gerar o conteúdo...")

    def _build_generate_tools(self) -> GenerateContentTools:
        """
        Create the content generation tools with the current app config.

        Returns:
            A configured ``GenerateContentTools`` instance.
        """
        return GenerateContentTools(config=self.get_config())

    def _generate_or_load_content(
        self,
        prompt: str,
        generate_content_tools: GenerateContentTools,
    ) -> Dict[str, Any] | None:
        """
        Generate real content or load fake content and normalize output.

        Args:
            prompt: User message that drives content generation.
            generate_content_tools: Tools instance used for real generation.

        Returns:
            A normalized dict with keys ``prompt``, ``content``,
            ``relevant_docs``, and ``latency`` when successful; ``None`` when
            generation/loading fails.

        Error Messages:
            - "Erro ao gerar conteúdo: {str(e)}"
        """
        try:
            with st.spinner("Gerando conteúdo..."):
                if self.fake_content:
                    generated_content = self._load_fake_content()
                    relevant_docs: List[str] = []
                    latency: float | None = None
                else:
                    generated_content, relevant_docs, latency = self._generate_content(
                        prompt,
                        generate_content_tools,
                    )
                    if generated_content is None:
                        return None

                return {
                    "prompt": prompt,
                    "content": generated_content,
                    "relevant_docs": relevant_docs,
                    "latency": latency,
                }
        except Exception as e:
            st.error(f"Erro ao gerar conteúdo: {str(e)}")
            return None

    def _generate_content(
        self,
        prompt: str,
        generate_content_tools: GenerateContentTools,
    ) -> Tuple[Any, List[str], float | None]:
        """
        Generate content via tools and collect metadata for UI rendering.

        Args:
            prompt: User message used as generation input.
            generate_content_tools: Configured tools facade that executes
                generation and exposes result accessors.

        Returns:
            A tuple ``(generated_content, relevant_docs, latency)``.
            On failure, returns ``(None, [], None)``.

        Error Messages:
            - "Failed to generate content: {str(e)}"
        """
        try:
            generate_content_tools.generate_content(prompt)
            generated_content = generate_content_tools.get_contents()
            relevant_docs = generate_content_tools.get_relevant_docs()
            latency = generate_content_tools.get_latency()
            return generated_content, relevant_docs, latency
        except Exception as e:
            st.error(f"Failed to generate content: {str(e)}")
            return None, [], None

    def _load_fake_content(self) -> Any:
        """
        Load mock content from disk for local demo/testing mode.

        Returns:
            Parsed JSON object from ``self.fake_content_path``.
        """
        with open(self.fake_content_path, "r") as file:
            generated_content = json.load(file)
        time.sleep(1)
        return generated_content

    def _append_generated_content(self, item: Dict[str, Any]) -> None:
        """
        Append a generated item to session-state history.

        Args:
            item: Normalized content item containing prompt, generated content,
                relevant docs, and latency.

        Returns:
            None.
        """
        st.session_state["generated_contents"].append(item)

    def _render_generated_contents(self) -> None:
        """
        Render all generated content entries stored in session state.

        For each history entry, this method normalizes shape differences,
        formats latency, creates an expander block, renders post markdown, and
        renders relevant-document badges.

        Returns:
            None.

        Error Messages:
            - "Erro ao renderizar conteúdos gerados: {str(e)}"
        """
        try:
            total_contents = len(st.session_state["generated_contents"])

            for index, item in enumerate(st.session_state["generated_contents"]):
                item_prompt, content, relevant_docs, item_latency = self._normalize_content_item(item)
                latency_label = self._format_latency(item_latency)

                if index == total_contents - 1:
                    st.markdown("<div id='last-content-expander'></div>", unsafe_allow_html=True)

                post_count = len(content) if isinstance(content, list) else 1
                expander_title = f"{post_count} Posts · **{item_prompt}** - {latency_label}"

                with st.expander(expander_title, expanded=index == total_contents - 1):
                    self._render_posts(content, index)
                    self._render_relevant_documents(relevant_docs)
        except Exception as e:
            st.error(f"Erro ao renderizar conteúdos gerados: {str(e)}")

    def _normalize_content_item(self, item: Any) -> Tuple[str, Any, List[str], Any]:
        """
        Normalize a history item to a render-friendly tuple shape.

        Args:
            item: Raw item from ``st.session_state['generated_contents']``.

        Returns:
            A tuple ``(item_prompt, content, relevant_docs, item_latency)``.
            If the item is not in the expected dict format, returns safe
            fallback values.

        Error Messages:
            - "Erro ao normalizar item de conteúdo: {str(e)}"
        """
        try:
            if isinstance(item, dict) and "content" in item:
                item_prompt = item.get("prompt", "(sem prompt)")
                content = item["content"]
                relevant_docs = item.get("relevant_docs", [])
                item_latency = item.get("latency")
                return item_prompt, content, relevant_docs, item_latency

            return "(prompt não disponível)", item, [], None
        except Exception as e:
            st.error(f"Erro ao normalizar item de conteúdo: {str(e)}")
            return "(erro ao normalizar)", item, [], None

    def _format_latency(self, item_latency: Any) -> str:
        """
        Format latency for display in the expander title.

        Args:
            item_latency: Raw latency value from generated metadata.

        Returns:
            A string in seconds with two decimals (e.g., ``"1.23s"``) or
            ``"N/A"`` when conversion is not possible.
        """
        try:
            return f"{float(item_latency):.2f}s" if item_latency is not None else "N/A"
        except (TypeError, ValueError):
            return "N/A"

    def _render_posts(self, content: Any, history_index: int) -> None:
        """
        Render one or multiple post blocks and copy actions.

        Args:
            content: Either a list of posts or a single post object.
            history_index: Index of the history item, used to build unique
                copy-button keys.

        Returns:
            None.

        Error Messages:
            - "Erro ao renderizar posts: {str(e)}"
        """
        try:
            posts = content if isinstance(content, list) else [content]

            for post_index, post in enumerate(posts):
                self._render_post_label(post_index)

                markdown_text = self.markdown_tools.generate_markdown(post)
                if not markdown_text:
                    continue

                st.markdown(markdown_text)
                self.markdown_tools.copy_markdown_button(
                    markdown_text,
                    button_key=f"copy_markdown_{history_index}_{post_index}",
                )

                if post_index < len(posts) - 1:
                    st.markdown("---")
        except Exception as e:
            st.error(f"Erro ao renderizar posts: {str(e)}")

    def _render_post_label(self, post_index: int) -> None:
        """
        Render the badge-like title for a post block.

        Args:
            post_index: Zero-based index of the post inside a history item.

        Returns:
            None.
        """
        st.markdown(
            f"""
            <div style="display:inline-block;padding:4px 10px;border:1px solid #d0d7de;border-radius:10px;background:#f6f8fa;font-weight:600;margin-bottom:8px;">
                Post {post_index + 1}
            </div>
            """,
            unsafe_allow_html=True,
        )

    def _render_relevant_documents(self, relevant_docs: List[str]) -> None:
        """
        Render relevant-document metadata for a generated item.

        Args:
            relevant_docs: List of relevant document names used as generation
                context.

        Returns:
            None.
        """
        st.markdown("---")
        st.markdown("**Documentos relevantes utilizados:**")

        if relevant_docs:
            docs_badges = "".join(
                [
                    (
                        "<span style='display:inline-block;padding:6px 12px;margin:4px;"
                        "border:1px solid #d0d7de;border-radius:9999px;background:#f6f8fa;"
                        f"font-size:0.9rem;'>{doc}</span>"
                    )
                    for doc in relevant_docs
                ]
            )
            st.markdown(f"<div>{docs_badges}</div>", unsafe_allow_html=True)
            st.write("")
            return

        st.write("Nenhum documento relevante encontrado.")

    def _scroll_to_last_content_if_needed(self, should_scroll: bool) -> None:
        """
        Scroll the page to the latest generated-content block when requested.

        Args:
            should_scroll: Whether the current rerun should trigger auto-scroll.
                This should only be ``True`` right after a new item is added.

        Returns:
            None.
        """
        total_contents = len(st.session_state["generated_contents"])
        if not should_scroll or total_contents == 0:
            return

        components.html(
            """
            <script>
            const el = window.parent.document.getElementById('last-content-expander');
            if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            </script>
            """,
            height=0,
        )
