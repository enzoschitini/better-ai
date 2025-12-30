import json
from typing import Any, List


class MarkdownStyle:
    def __init__(self):
        self.divider = ""
        self.key_prefix = "### "


class JsonToMarkdownRenderer:
    def __init__(self, style: MarkdownStyle):
        self.style = style
        self.lines: List[str] = []

    def render(self, data: Any, title: str | None = None) -> str:
        self.lines = []

        if title:
            self.lines.append(f"# {title}")
            self.lines.append("")

        self._render_any(data, is_root=True)

        return "\n".join(self.lines).strip() + "\n"

    def _render_any(self, data: Any, is_root: bool = False):
        if isinstance(data, dict):
            self._render_dict(data, is_root)

        elif isinstance(data, list):
            self._render_list(data)

        else:
            self._render_value(data)

    def _render_dict(self, data: dict, is_root: bool):
        for key, value in data.items():
            formatted_key = self._format_key(key)
            self.lines.append(f"{self.style.key_prefix}{formatted_key}")
            self._render_any(value)

        # Divider solo tra blocchi principali
        if is_root:
            self._append_divider()

    def _render_list(self, data: list):
        for index, item in enumerate(data):
            if index > 0:
                self._append_divider()
            self._render_any(item, is_root=True)

    def _render_value(self, value: Any):
        self.lines.append(str(value))

    def _append_divider(self):
        if not self.lines or self.lines[-1] == self.style.divider:
            return
        self.lines.append("")
        self.lines.append(self.style.divider)
        self.lines.append("")

    @staticmethod
    def _format_key(key: str) -> str:
        """
        contexto_da_mencao -> **Contexto da mencao**
        """
        readable = key.replace("_", " ").capitalize()
        return f"**{readable}**"


class JsonToMarkdownConverter:
    def __init__(self):
        self.style = MarkdownStyle()
        self.renderer = JsonToMarkdownRenderer(self.style)

    def load_json(self, path: str) -> Any:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_markdown(self, content: str, output_path: str):
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

    def run(
        self,
        input_json_path: str,
        output_md_path: str,
        title: str = "Analisi delle Menzioni"
    ):
        data = self.load_json(input_json_path)
        markdown = self.renderer.render(data, title)
        self.save_markdown(markdown, output_md_path)


if __name__ == "__main__":
    converter = JsonToMarkdownConverter()
    converter.run(
        input_json_path="src/text_classifier/output_n8n.json",
        output_md_path="output.md",
        title="Analisi delle Menzioni"
    )
