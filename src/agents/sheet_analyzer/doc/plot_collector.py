import os
import uuid
import base64
from io import BytesIO

import matplotlib.pyplot as plt
from src.agents.sheet_analyzer.doc.config import AgentConfig


class PlotCollector:
    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = output_dir
        self.graphs = []

        os.makedirs(self.output_dir, exist_ok=True)

    def custom_show(self):
        buffer = BytesIO()
        filename = f"{self.output_dir}/plot_{uuid.uuid4().hex}.png"

        plt.savefig(filename)
        plt.savefig(buffer, format="png")
        plt.close()

        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode("utf-8")

        graph_data = {
            "file_path": filename,
            "image_base64": img_base64[:100]  # preview
        }

        self.graphs.append(graph_data)

        return graph_data

    def patch_matplotlib(self):
        plt.show = self.custom_show  # 🔥 monkey patch

    def reset(self):
        self.graphs = []

    def get_graphs(self):
        return self.graphs
