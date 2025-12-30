from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.colors import black, grey


class JsonPdfStyle:
    def __init__(self):
        base = getSampleStyleSheet()

        self.title = ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontSize=18,
            spaceAfter=16
        )

        self.key = ParagraphStyle(
            "Key",
            fontSize=11,
            fontName="Helvetica-Bold",
            underline=True,
            spaceBefore=6,
            spaceAfter=2
        )

        self.value = ParagraphStyle(
            "Value",
            fontSize=10,
            fontName="Helvetica",
            leftIndent=12,
            spaceAfter=6
        )

        self.list_item = ParagraphStyle(
            "ListItem",
            fontSize=10,
            leftIndent=18,
            spaceAfter=4
        )

        self.divider = ParagraphStyle(
            "Divider",
            fontSize=8,
            textColor=grey,
            spaceBefore=10,
            spaceAfter=10,
            alignment=TA_LEFT
        )


from typing import Any, List
from reportlab.platypus import Paragraph, Spacer

class JsonToPdfRenderer:
    def __init__(self, styles: JsonPdfStyle):
        self.styles = styles
        self.elements: List[Any] = []

    def render(self, data: Any, title: str = None):
        if title:
            self.elements.append(Paragraph(title, self.styles.title))
            self.elements.append(Spacer(1, 12))

        self._render_any(data)

        return self.elements

    def _render_any(self, data: Any):
        if isinstance(data, dict):
            self._render_dict(data)

        elif isinstance(data, list):
            self._render_list(data)

        else:
            self.elements.append(
                Paragraph(str(data), self.styles.value)
            )

    def _render_dict(self, data: dict):
        for key, value in data.items():
            self.elements.append(
                Paragraph(str(key), self.styles.key)
            )
            self._render_any(value)

        self._add_divider()

    def _render_list(self, data: list):
        for idx, item in enumerate(data, start=1):
            self.elements.append(
                Paragraph(f"• Elemento {idx}", self.styles.list_item)
            )
            self._render_any(item)

    def _add_divider(self):
        self.elements.append(
            Paragraph("—" * 40, self.styles.divider)
        )


import json
from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.pagesizes import A4

class JsonToPdfConverter:
    def __init__(self, page_size=A4):
        self.page_size = page_size
        self.styles = JsonPdfStyle()
        self.renderer = JsonToPdfRenderer(self.styles)

    def load_json(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def run(
        self,
        input_json_path: str,
        output_pdf_path: str,
        title: str = "Report JSON"
    ):
        data = self.load_json(input_json_path)

        doc = SimpleDocTemplate(
            output_pdf_path,
            pagesize=self.page_size,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        elements = self.renderer.render(data, title)
        doc.build(elements)


if __name__ == "__main__":
    converter = JsonToPdfConverter()
    converter.run(
        input_json_path="src/text_classifier/output_n8n.json",
        output_pdf_path="output.pdf",
        title="Analisi delle Menzioni"
    )
