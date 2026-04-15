import os
import pandas as pd
from pandasai import Agent
from pandasai.llm import OpenAI
from io import BytesIO
import logging
from dotenv import load_dotenv
from src.dataframe_analyzers.pd_df_agent.plot_collector import PlotCollector

collector = PlotCollector(output_dir="charts", save=True)
collector.patch_matplotlib()

# LOGS (nível sistema)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

load_dotenv()

llm = OpenAI()

with open("src\\agents\\sheet_analyzer\\sheets\\ENQUETE_OTB_ACAOPROMO.xlsx", "rb") as f:
    file_bytes = f.read()

df = pd.DataFrame({
    "country": ["United States", "United Kingdom", "France", "Germany", "Italy", "Spain", "Canada", "Australia", "Japan", "China"],
    "sales": [5000, 3200, 2900, 4100, 2300, 2100, 2500, 2600, 4500, 7000]
})

df = pd.read_excel(BytesIO(file_bytes))

# LLM (controlado)
llm = OpenAI(
    temperature=0,        # determinístico
    max_tokens=1000
)

# 🧠 AGENT
agent = Agent(
    df,
    config={
        # 🔑 LLM
        "llm": llm,
        "temperature": 0,

        # 🔁 Robustez
        "max_retries": 3,

        # 🪵 Debug
        "verbose": True,
        "save_logs": True,

        # 📊 Output (v2)
        "save_charts": False,
        "save_charts_path": "src/dataframe_analyzers/pandas_ai/charts",
        "open_charts": False,

        # ⚙️ Execução (v2)
        "enable_cache": False,
    },
    memory_size=5,                # contexto curto (evita confusão)
    description="""
    You are a senior data analyst.

    RULES:
    - Always validate calculations before answering
    - Prefer structured outputs (tables, lists)
    - Never hallucinate data
    - If unsure, explicitly say assumptions
    - Keep answers concise and precise
    """
)

# WRAPPER SEGURO
def ask_agent(question: str):
    try:
        print(f"\nPergunta: {question}")

        # 🔄 limpa gráficos anteriores
        collector.reset()

        result = agent.chat(question)

        print("\nResultado:")
        print(result)

        # 🔍 DEBUG
        print("\nCódigo gerado:")
        print(agent.last_code_generated)

        # 📊 coleta gráficos
        graphs = collector.get_graphs()

        print(f"\n📊 Gráficos gerados: {len(graphs)}")

        for i, g in enumerate(graphs):
            print(f"\nGraph {i+1}:")
            print("file_path:", g["file_path"])
            print("base64_preview:", g["image_base64"])

        return {
            "result": result,
            "graphs": graphs
        }

    except Exception as e:
        print("\nErro controlado:", e)

        if hasattr(agent, "last_code_generated"):
            print("\nÚltimo código gerado:")
            print(agent.last_code_generated)

        return None


if __name__ == "__main__":
    while True:
        q = input("\nDigite sua pergunta (ou 'cls' para limpar): ")

        if q.lower() == "cls":
            break

        ask_agent(q)


# python -m src.dataframe_analyzers.pandas_ai.test2