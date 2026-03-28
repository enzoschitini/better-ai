
from src.dev_tools.doc_class.agent import GenereteDoc
from src.dev_tools.doc_class.menage_files import TxtLoader, MarkdownSaver
from src.dev_tools.doc_class.config import AgentConfig

class ClassDoc:
    def __init__(self):
        config = AgentConfig()
        self.path = config.path

    def load_code(self):
        try:
            loader = TxtLoader()
            return loader.load(f"{self.path}/code.txt")
        except Exception as e:
            raise RuntimeError("Erro: ClassDoc.load_code", str(e))

    def _generate_doc(self, code: str):
        try:
            gen = GenereteDoc()

            docstring = gen.generate_doc_string(code)
            documentation = gen.generate_doc_class(docstring)

            return docstring, documentation

        except Exception as e:
            raise RuntimeError("Erro: ClassDoc._generate_doc", str(e))

    def save_markdown(self, documentation: str, name: str):
        try:
            saver = MarkdownSaver()
            saver.save(documentation, f"{self.path}/{name}.md")
            print("Doc generated")
        except Exception as e:
            raise RuntimeError("Erro: ClassDoc.save_markdown", str(e))

    def run(self):
        try:
            code = self.load_code()
            docstring, documentation = self._generate_doc(code)
            self.save_markdown(docstring, "docstring")
            self.save_markdown(documentation, "documentation")

        except Exception as e:
            raise RuntimeError("Erro: ClassDoc.generate_doc", str(e))

if __name__ == "__main__":
    import time
    start = time.perf_counter()

    ClassDoc().run()

    end = time.perf_counter()
    duration = end - start

    print(f"Tempo de execução: {duration:.2f} segundos")

# python -m src.dev_tools.doc_class.module