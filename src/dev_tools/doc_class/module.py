
from src.dev_tools.doc_class.agent import GenereteDoc
from src.dev_tools.doc_class.menage_files import TxtLoader, MarkdownSaver

class ClassDoc:
    def __init__(self):
        pass

    def load_code(self):
        try:
            loader = TxtLoader()
            return loader.load("src/dev_tools/doc_class/code.txt")
        except Exception as e:
            raise RuntimeError("Erro: ClassDoc.load_code", str(e))

    def _generate_doc(self, code: str):  # 👈 renomeado
        try:
            gen = GenereteDoc()

            docstring = gen.generate_doc_string(code)
            documentation = gen.generate_doc_class(docstring)

            return documentation

        except Exception as e:
            raise RuntimeError("Erro: ClassDoc._generate_doc", str(e))

    def save_markdown(self, documentation: str):
        try:
            saver = MarkdownSaver()
            saver.save(documentation, "src/dev_tools/doc_class/doc.md")
            print("Doc generated")
        except Exception as e:
            raise RuntimeError("Erro: ClassDoc.save_markdown", str(e))

    def run(self):  # 👈 método principal
        try:
            code = self.load_code()
            documentation = self._generate_doc(code)  # 👈 corrigido
            self.save_markdown(documentation)

        except Exception as e:
            raise RuntimeError("Erro: ClassDoc.generate_doc", str(e))

if __name__ == "__main__":
    import time
    start = time.perf_counter()

    ClassDoc().run()

    end = time.perf_counter()
    duration = end - start

    print(f"Tempo de execução: {duration:.4f} segundos")

# python -m src.dev_tools.doc_class.module