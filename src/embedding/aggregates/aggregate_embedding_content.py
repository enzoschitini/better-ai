
class AggregateEmbeddingContent:
    def __init__(self, payload, pipeline, file_content):
        self.payload = payload
        self.pipeline = pipeline
        self.file_content = file_content

    def process(self):
        additional_content = {
            "summary": "This is additional content generated from the pipeline.",
            "generated_tags": "#finance, #report, #2026"
        }

        prepared_content = {
            "file_content": self.file_content,
            **(additional_content if self.pipeline else {})
        }

        return prepared_content

