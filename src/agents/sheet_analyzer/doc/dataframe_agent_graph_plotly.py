import os
import uuid
import base64
from io import BytesIO

import pandas as pd
import plotly.express as px

from dotenv import load_dotenv
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_experimental.agents import create_pandas_dataframe_agent

load_dotenv()

# =========================
# 📁 Pasta outputs
# =========================
os.makedirs("outputs", exist_ok=True)

# =========================
# 📦 Storage
# =========================
GRAPHS = []

# =========================
# 🎯 Função central de gráfico
# =========================
def create_plotly_chart(params: dict) -> str:
    """
    Tool segura para criação de gráficos
    """
    global GRAPHS

    chart_type = params.get("chart_type")
    x = params.get("x")
    y = params.get("y")
    title = params.get("title", "")

    if chart_type == "bar":
        # 🔥 agregação automática
        df_counts = df[x].value_counts().reset_index()
        df_counts.columns = [x, "count"]

        fig = px.bar(df_counts, x=x, y="count", title=title)

    else:
        return "Unsupported chart type"

    # =========================
    # 💾 Salvar gráfico
    # =========================
    graph_id = uuid.uuid4().hex

    html_path = f"outputs/plot_{graph_id}.html"
    png_path = f"outputs/plot_{graph_id}.png"

    fig.write_html(html_path)
    fig.write_image(png_path)

    buffer = BytesIO()
    fig.write_image(buffer, format="png")
    buffer.seek(0)

    img_base64 = base64.b64encode(buffer.read()).decode("utf-8")

    graph_data = {
        "type": "plotly",
        "html_path": html_path,
        "image_base64": img_base64[:100]
    }

    GRAPHS.append(graph_data)

    return "Chart created successfully"

# =========================
# 🛠 Tool wrapper
# =========================
def plot_tool(input: str) -> str:
    import json
    params = json.loads(input)
    return create_plotly_chart(params)

plotly_tool = Tool(
    name="plot_chart",
    func=plot_tool,
    description="""
Create charts using the dataframe.

Input must be JSON with:
{
    "chart_type": "bar",
    "x": "column_name",
    "title": "chart title"
}
"""
)

# =========================
# 🤖 LLM
# =========================
model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

# =========================
# 📊 DataFrame
# =========================
df = pd.read_csv("src/agents/sheet_analyzer/doc/titanic.csv")

# =========================
# 🧠 Agent
# =========================
agent = create_pandas_dataframe_agent(
    llm=model,
    df=df,
    agent_type="tool-calling",
    extra_tools=[plotly_tool],

    prefix="""
You are a professional data analyst working with a pandas DataFrame called `df`.

Rules:
- ALWAYS use the provided dataframe
- NEVER create charts manually

CRITICAL:
- To create charts, you MUST use the tool `plot_chart`
- DO NOT use matplotlib
- DO NOT use plotly directly

Guidelines:
- For distributions, use:
    chart_type = "bar"
    x = column name

- Always verify column names using df.columns
""",

    suffix="""
Provide a clear analysis.

IMPORTANT:
- Do NOT mention charts creation
- Assume charts are already visible
- Focus only on insights
""",

    include_df_in_prompt=True,
    number_of_head_rows=5,

    max_execution_time=15,
    early_stopping_method="force",

    allow_dangerous_code=True,
    verbose=True,
)

# =========================
# 🚀 RUN
# =========================
if __name__ == "__main__":
    import json

    GRAPHS = []

    response = agent.invoke(
        "Create a bar chart showing the number of passengers per Pclass"
    )

    final_response = {
        "input": response["input"],
        "graphs": GRAPHS,
        "output": response["output"]
    }

    print(json.dumps(final_response, indent=4))