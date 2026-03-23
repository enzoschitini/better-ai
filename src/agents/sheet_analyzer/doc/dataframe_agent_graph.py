import os
import uuid
import base64
from io import BytesIO

import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv

from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_experimental.agents import create_pandas_dataframe_agent

load_dotenv()

# =========================
# 📁 Garantir pasta outputs
# =========================
os.makedirs("outputs", exist_ok=True)

GRAPHS = []

# =========================
# 🎯 Monkey patch do plt.show()
# =========================
def custom_show():
    global GRAPHS

    buffer = BytesIO()
    filename = f"outputs/plot_{uuid.uuid4().hex}.png"

    plt.savefig(filename)
    plt.savefig(buffer, format='png')
    plt.close()

    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')

    graph_data = {
        "file_path": filename,
        "image_base64": img_base64[:100]
    }

    GRAPHS.append(graph_data)

    return graph_data

plt.show = custom_show  # 🔥 sobrescreve comportamento

# =========================
# 🤖 LLM
# =========================
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# =========================
# 📊 DataFrame
# =========================
df = pd.read_csv("src/agents/sheet_analyzer/doc/titanic.csv")

# =========================
# 🛠 Tool custom
# =========================
def custom_calculation_tool(input: str) -> str:
    return f"Custom calculation result for: {input}"

extra_tools = [
    Tool(
        name="custom_calculation",
        func=custom_calculation_tool,
        description="A tool for performing custom calculations."
    )
]

# =========================
# 🧠 Agent
# =========================
agent = create_pandas_dataframe_agent(
    llm=model,
    df=df,
    agent_type="tool-calling",
    extra_tools=extra_tools,

    prefix="""
You are a data analyst working with a pandas DataFrame called `df`.

Rules:
- ALWAYS use the provided dataframe `df`
- NEVER load external datasets

When creating plots:
- ALWAYS use matplotlib
- ALWAYS call plt.show() at the end
""",

    suffix="""
Provide the final answer clearly.

IMPORTANT:
- Do NOT include any image links, file paths, or markdown images
- Do NOT mention where the chart is saved
- Assume the chart is already displayed in the interface
- Only describe the insights from the chart
""",

    include_df_in_prompt=True,
    number_of_head_rows=5,

    max_execution_time=10,
    early_stopping_method="force",

    allow_dangerous_code=True,
    verbose=True,
)

# =========================
# 🚀 Run
# =========================
if __name__ == "__main__":
    import json

    # reset collector
    GRAPHS = []

    response = agent.invoke(
        "Create a bar chart showing the number of passengers in each class."
    )

    final_response = {
        "input": response["input"],
        "graphs": GRAPHS,
        "output": response["output"]
    }

    print(json.dumps(final_response, indent=4))