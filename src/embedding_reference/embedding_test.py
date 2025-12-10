from src.embedding_reference.file_content_extractor import FileContentExtractor
from io import BytesIO
import os

ALLOWED_EXTENSIONS = {
    "txt", "md", "markdown", "html",
    "pdf", "doc", "docx", "ppt", "pptx",
    "csv", "xls", "xlsx", "xml", "json"
}

BASE_DIR = "src/embedding_reference/files/"


def load_file_bytes(filename: str):
    """
    Carrega qualquer arquivo da pasta /src/embedding_reference/files/
    e retorna um BytesIO + extensão válida.
    """
    file_path = os.path.join(BASE_DIR, filename)

    # Valida caminho
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

    # Valida extensão
    ext = filename.lower().split(".")[-1]
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Extensão não suportada: .{ext}")

    # Lê bytes
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    # Transforma em BytesIO
    file_bytes_io = BytesIO(file_bytes)

    return file_bytes_io, ext


def extract_file_content(filename: str):
    """
    Carrega arquivo → transforma em BytesIO → extrai conteúdo
    """
    try:
        file_bytes_io, ext = load_file_bytes(filename)
        extractor = FileContentExtractor(file_bytes_io, ext)
        return extractor.extract()

    except Exception as e:
        print(f"❌ Error processing file '{filename}': {e}")
        raise


# ---- TESTE ----
result = extract_file_content("example.txt")
print(result)










# python -m src.embedding_reference.embedding_test
"""
extensoes = [
    "txt",
    "md",
    "markdown",
    "html",
    "pdf",
                    "doc", *
    "docx",
                    "ppt", *
    "pptx",
    "csv",
                    "xls", *
    "xlsx",
                    "xml", *
    "json",
]

"""