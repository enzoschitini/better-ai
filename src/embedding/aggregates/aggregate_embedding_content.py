
class AggregateEmbeddingContent:
    def __init__(self, pipeline):
        self.pipeline = pipeline

    def process(self):
        return {
            "additional_content": "This is additional content generated from the pipeline.",
            "generated_tags": "#finance, #report, #2026"
        }
