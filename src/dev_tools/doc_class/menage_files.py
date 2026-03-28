
from pathlib import Path


class TxtLoader:
    def __init__(self, encoding: str = "utf-8"):
        self.encoding = encoding

    def load(self, file_path: str) -> str:
        """
        Carrega todo o conteúdo de um arquivo TXT.
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        if path.suffix != ".txt":
            raise ValueError("O arquivo precisa ser do tipo .txt")

        with path.open("r", encoding=self.encoding) as file:
            return file.read()

    def load_lines(self, file_path: str) -> list[str]:
        """
        Carrega o arquivo TXT e retorna uma lista de linhas.
        """
        content = self.load(file_path)
        return content.splitlines()

    def load_as_chunks(self, file_path: str, chunk_size: int = 500) -> list[str]:
        """
        Divide o texto em chunks de tamanho fixo (útil para NLP).
        """
        content = self.load(file_path)
        return [
            content[i:i + chunk_size]
            for i in range(0, len(content), chunk_size)
        ]

from pathlib import Path


class MarkdownSaver:
    def __init__(self, encoding: str = "utf-8"):
        self.encoding = encoding

    def save(self, content: str, file_path: str) -> None:
        """
        Salva um texto em um arquivo Markdown (.md).
        """
        path = Path(file_path)

        if path.suffix != ".md":
            raise ValueError("O arquivo precisa ter extensão .md")

        # Cria diretórios se não existirem
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding=self.encoding) as file:
            file.write(content)

    def append(self, content: str, file_path: str) -> None:
        """
        Adiciona conteúdo ao final de um arquivo Markdown existente.
        """
        path = Path(file_path)

        if path.suffix != ".md":
            raise ValueError("O arquivo precisa ter extensão .md")

        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("a", encoding=self.encoding) as file:
            file.write(content)

    def save_with_title(self, title: str, content: str, file_path: str) -> None:
        """
        Salva o conteúdo já formatado com um título Markdown (# Título).
        """
        markdown_content = f"# {title}\n\n{content}"
        self.save(markdown_content, file_path)


"""
loader = TxtLoader()

texto = loader.load("src/dev_tools/doc_class/code.txt")
print(texto)
"""

"""
saver = MarkdownSaver()

texto = '''
## Introdução
Esse é um conteúdo em markdown.

- Item 1
- Item 2
'''

saver.save(texto, "src/dev_tools/doc_class/doc.md")
"""

# python -m src.dev_tools.doc_class.menage_files    