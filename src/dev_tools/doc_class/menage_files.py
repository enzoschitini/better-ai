
from pathlib import Path

class TxtLoader:
    def __init__(self, encoding: str = "utf-8"):
        self.encoding = encoding

    def load(self, file_path: str) -> str:
        """
        Carrega todo o conteúdo de um arquivo TXT.
        """
        try:
            path = Path(file_path)

            if not path.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

            if path.suffix != ".txt":
                raise ValueError("O arquivo precisa ser do tipo .txt")

            with path.open("r", encoding=self.encoding) as file:
                return file.read()
        
        except Exception as e:
            raise RuntimeError("Erro: TxtLoader.load", str(e))

    def load_lines(self, file_path: str) -> list[str]:
        """
        Carrega o arquivo TXT e retorna uma lista de linhas.
        """
        try:
            content = self.load(file_path)
            return content.splitlines()

        except Exception as e:
            raise RuntimeError("Erro: TxtLoader.load_lines", str(e))

    def load_as_chunks(self, file_path: str, chunk_size: int = 500) -> list[str]:
        """
        Divide o texto em chunks de tamanho fixo (útil para NLP).
        """
        try:
            content = self.load(file_path)
            return [
                content[i:i + chunk_size]
                for i in range(0, len(content), chunk_size)
            ]

        except Exception as e:
            raise RuntimeError("Erro: TxtLoader.load_as_chunks", str(e))


class MarkdownSaver:
    def __init__(self, encoding: str = "utf-8"):
        self.encoding = encoding

    def save(self, content: str, file_path: str) -> None:
        """
        Salva um texto em um arquivo Markdown (.md).
        """
        try:
            path = Path(file_path)

            if path.suffix != ".md":
                raise ValueError("O arquivo precisa ter extensão .md")

            # Cria diretórios se não existirem
            path.parent.mkdir(parents=True, exist_ok=True)

            with path.open("w", encoding=self.encoding) as file:
                file.write(content)

        except Exception as e:
            raise RuntimeError("Erro: MarkdownSaver.save", str(e))

    def append(self, content: str, file_path: str) -> None:
        """
        Adiciona conteúdo ao final de um arquivo Markdown existente.
        """
        try:
            path = Path(file_path)

            if path.suffix != ".md":
                raise ValueError("O arquivo precisa ter extensão .md")

            path.parent.mkdir(parents=True, exist_ok=True)

            with path.open("a", encoding=self.encoding) as file:
                file.write(content)

        except Exception as e:
            raise RuntimeError("Erro: MarkdownSaver.append", str(e))

    def save_with_title(self, title: str, content: str, file_path: str) -> None:
        """
        Salva o conteúdo já formatado com um título Markdown (# Título).
        """
        try:
            markdown_content = f"# {title}\n\n{content}"
            self.save(markdown_content, file_path)

        except Exception as e:
            raise RuntimeError("Erro: MarkdownSaver.save_with_title", str(e))

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