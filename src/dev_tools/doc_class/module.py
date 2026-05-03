import time

from src.dev_tools.doc_class.agent import GenereteDoc
from src.dev_tools.doc_class.menage_files import TxtLoader, MarkdownSaver
from src.dev_tools.doc_class.config import AgentConfig
from src.tracing.tracing_core import ApplicationTracing

tracer = ApplicationTracing(
    log_id="null",
    flag="Doc",
    file_name="module.py",
    log_file_name="doc",
    show_info_logs=True,
)

class ClassDoc:
    def __init__(self, class_name: str = "output"):
        tracer.INFO("Initializing")
        config = AgentConfig()
        self.path = config.path
        self.class_name = class_name

    def load_code(self):
        try:
            loader = TxtLoader()
            code = loader.load(f"{self.path}/code.txt")

            tracer.INFO("Code loaded")
            return code
        except Exception as e:
            raise RuntimeError("Erro: ClassDoc.load_code", str(e))

    def _generate_doc(self, code: str):
        try:
            gen = GenereteDoc()

            tracer.INFO("Generating docstring")
            docstring = gen.generate_doc_string(code)
            tracer.INFO("Docstring generated successfully.")

            tracer.INFO("Generating documentation")
            documentation = gen.generate_doc_class(docstring)
            tracer.INFO("Documentation successfully generated.")

            return docstring, documentation

        except Exception as e:
            raise RuntimeError("Erro: ClassDoc._generate_doc", str(e))

    def save_markdown(self, documentation: str, name: str):
        try:
            saver = MarkdownSaver()
            saver.save(documentation, f"{self.path}/{self.class_name}/{name}.md")
        except Exception as e:
            raise RuntimeError("Erro: ClassDoc.save_markdown", str(e))

    def run(self):
        try:
            start = time.perf_counter()

            code = self.load_code()
            docstring, documentation = self._generate_doc(code)

            self.save_markdown(docstring, "docstring")
            tracer.INFO("Docstring saved successfully")

            self.save_markdown(documentation, "documentation")
            tracer.INFO("Documentation saved successfully.")

            end = time.perf_counter()
            duration = end - start

            tracer.INFO("Process completed successfully.")
            tracer.INFO(f"Execution time: {duration:.2f} seconds")

        except Exception as e:
            raise RuntimeError("Erro: ClassDoc.generate_doc", str(e))

if __name__ == "__main__":
    ClassDoc("PineconeVectorStore").run()

# python -m src.dev_tools.doc_class.module