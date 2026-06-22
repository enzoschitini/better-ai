import uuid
import base64
from io import BytesIO

import matplotlib
# Force a non-GUI backend to avoid Tkinter thread errors on server/worker execution.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from src.tracing.tracing_core import ApplicationTracing

tracer = ApplicationTracing(
    flag="DataframeAgent",
    file_name="plot_collector.py",
    log_file_name="dataframe_agent"
)

class PlotCollector:
    def __init__(self):
        self.graphs = []

        tracer.INFO(
            message="PlotCollector initialized",
            metadata={"mode": "base64_only"}
        )

    def custom_show(self):
        buffer = BytesIO()
        figure = plt.gcf()

        # Gera imagem em memória
        figure.savefig(buffer, format="png")
        plt.close(figure)

        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode("utf-8")

        graph_data = {
            "file_name": f"plot_{uuid.uuid4().hex}.png",
            "image_base64": img_base64
        }

        self.graphs.append(graph_data)

        tracer.INFO(
            message="Graph collected",
            metadata={
                "file_name": graph_data["file_name"],
                "base64_preview": img_base64[:100]
            }
        )

        return graph_data

    def patch_matplotlib(self):
        plt.show = self.custom_show
        tracer.INFO(message="Matplotlib patched to use custom show method")

    def reset(self):
        tracer.INFO(
            message=f"Resetting PlotCollector, clearing {len(self.graphs)} collected graphs"
        )
        self.graphs = []

    def get_graphs(self):
        tracer.INFO(
            message=f"Retrieving {len(self.graphs)} collected graphs"
        )
        return self.graphs

# python -m src.dataframe_analyzers.pd_df_agent.plot_collector