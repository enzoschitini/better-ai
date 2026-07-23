import json
import time

from typing import Any, Callable, Dict, List, Tuple

import streamlit as st
import streamlit.components.v1 as components

from src.web_applications.pages.content_generator.generate_content_tools import GenerateContentTools


class Chat:
    def __init__(
        self,
        get_config: Callable[[], Dict[str, Any]],
        markdown_tools: Any,
        fake_content: bool = False,
        fake_content_path: str = "src/web_applications/applications/post.json",
    ) -> None:
        self.get_config = get_config
        self.markdown_tools = markdown_tools
        self.fake_content = fake_content
        self.fake_content_path = fake_content_path

    def chat(self) -> None:
        prompt = self._get_prompt()
        generate_content_tools = self._build_generate_tools()

        if prompt:
            generated_item = self._generate_or_load_content(prompt, generate_content_tools)
            if generated_item is None:
                return

            self._append_generated_content(generated_item)
            st.session_state["scroll_to_last_content"] = True

        self._render_generated_contents()
        self._scroll_to_last_content_if_needed()

    def _get_prompt(self) -> str:
        return st.chat_input("Digite algo para gerar o conteúdo...")

    def _build_generate_tools(self) -> GenerateContentTools:
        return GenerateContentTools(config=self.get_config())

    def _generate_or_load_content(
        self,
        prompt: str,
        generate_content_tools: GenerateContentTools,
    ) -> Dict[str, Any] | None:
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

    def _generate_content(
        self,
        prompt: str,
        generate_content_tools: GenerateContentTools,
    ) -> Tuple[Any, List[str], float | None]:
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
        with open(self.fake_content_path, "r") as file:
            generated_content = json.load(file)
        time.sleep(1)
        return generated_content

    def _append_generated_content(self, item: Dict[str, Any]) -> None:
        st.session_state["generated_contents"].append(item)

    def _render_generated_contents(self) -> None:
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

    def _normalize_content_item(self, item: Any) -> Tuple[str, Any, List[str], Any]:
        if isinstance(item, dict) and "content" in item:
            item_prompt = item.get("prompt", "(sem prompt)")
            content = item["content"]
            relevant_docs = item.get("relevant_docs", [])
            item_latency = item.get("latency")
            return item_prompt, content, relevant_docs, item_latency

        return "(prompt não disponível)", item, [], None

    def _format_latency(self, item_latency: Any) -> str:
        try:
            return f"{float(item_latency):.2f}s" if item_latency is not None else "N/A"
        except (TypeError, ValueError):
            return "N/A"

    def _render_posts(self, content: Any, history_index: int) -> None:
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

    def _render_post_label(self, post_index: int) -> None:
        st.markdown(
            f"""
            <div style="display:inline-block;padding:4px 10px;border:1px solid #d0d7de;border-radius:10px;background:#f6f8fa;font-weight:600;margin-bottom:8px;">
                Post {post_index + 1}
            </div>
            """,
            unsafe_allow_html=True,
        )

    def _render_relevant_documents(self, relevant_docs: List[str]) -> None:
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

    def _scroll_to_last_content_if_needed(self) -> None:
        total_contents = len(st.session_state["generated_contents"])
        if not st.session_state["scroll_to_last_content"] or total_contents == 0:
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
        st.session_state["scroll_to_last_content"] = False
