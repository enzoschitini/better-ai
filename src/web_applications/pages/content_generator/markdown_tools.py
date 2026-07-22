import json
import streamlit.components.v1 as components


class MarkdownTools:
    def generate_markdown(self, post_data: dict) -> str:
        if not isinstance(post_data, dict):
            return ""

        markdown = f"# {post_data.get('title', '')}\n\n"
        markdown += f"{post_data.get('summary', '')}\n\n"
        markdown += f"{post_data.get('body', '')}\n\n"
        markdown += f"**Call to Action:** {post_data.get('cta', '')}\n\n"
        markdown += "### Hashtags\n"
        for hashtag in post_data.get('hashtags', []):
            markdown += f"{hashtag} "
        markdown += "\n\n"
        markdown += "### Sources Used\n"
        for source in post_data.get('sources_used', []):
            markdown += f"- {source}\n"

        return markdown

    def copy_markdown_button(self, markdown_text: str, button_key: str):
        button_id = f"copy_btn_{button_key}"
        status_id = f"copy_status_{button_key}"

        components.html(
            f"""
            <div style="margin: 6px 0 2px 0;">
                <button id="{button_id}" style="padding: 6px 12px; border-radius: 8px; border: 1px solid #d0d7de; background: #f6f8fa; cursor: pointer;">
                    Copiar Markdown
                </button>
                <span id="{status_id}" style="margin-left: 8px; color: #2e7d32; font-size: 0.9rem;"></span>
            </div>
            <script>
            const text = {json.dumps(markdown_text)};
            const btn = document.getElementById('{button_id}');
            const status = document.getElementById('{status_id}');

            function showStatus(message) {{
                status.textContent = message;
                setTimeout(() => {{
                    status.textContent = '';
                }}, 2000);
            }}

            async function copyText() {{
                status.textContent = '';
                try {{
                    if (navigator.clipboard && navigator.clipboard.writeText) {{
                        await navigator.clipboard.writeText(text);
                        showStatus('Copiado');
                        return;
                    }}
                }} catch (e) {{
                    // fallback below
                }}

                const textarea = document.createElement('textarea');
                textarea.value = text;
                textarea.style.position = 'fixed';
                textarea.style.opacity = '0';
                document.body.appendChild(textarea);
                textarea.focus();
                textarea.select();

                try {{
                    const ok = document.execCommand('copy');
                    showStatus(ok ? 'Copiado' : 'Falha ao copiar');
                }} catch (e) {{
                    showStatus('Falha ao copiar');
                }}

                document.body.removeChild(textarea);
            }}

            btn.addEventListener('click', copyText);
            </script>
            """,
            height=52,
        )

