import json
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def json_to_pdf(data, output_path="output.pdf"):
    styles = getSampleStyleSheet()

    pdf = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    story = []

    def render(obj, level=0):
        indent = "&nbsp;" * 4 * level

        if isinstance(obj, dict):
            for key, value in obj.items():
                story.append(
                    Paragraph(f"{indent}<b>{key}</b>:", styles["Normal"])
                )
                story.append(Spacer(1, 4))
                render(value, level + 1)

        elif isinstance(obj, list):
            for i, item in enumerate(obj, 1):
                story.append(
                    Paragraph(f"{indent}<b>- Item {i}</b>", styles["Normal"])
                )
                render(item, level + 1)

        else:
            story.append(
                Paragraph(f"{indent}{str(obj)}", styles["Normal"])
            )
            story.append(Spacer(1, 6))

    render(data)
    pdf.build(story)


if __name__ == "__main__":
    with open("src/text_classifier/template_base/output.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    json_to_pdf(data, "resultado.pdf")
    print("PDF gerado com sucesso.")
