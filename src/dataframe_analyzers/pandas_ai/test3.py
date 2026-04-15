import os
import logging
import pandas as pd
from io import BytesIO
from dotenv import load_dotenv

from pandasai import Agent
from pandasai.llm import OpenAI

# 🔥 PATCH CRÍTICO (corrige erro de plot)
from pandasai.responses.response_serializer import ResponseSerializer

_original_serialize = ResponseSerializer.serialize

def safe_serialize(result):
    if isinstance(result, dict) and result.get("type") == "plot":
        return {
            "type": "plot",
            "value": "handled_by_plot_collector"
        }
    return _original_serialize(result)

ResponseSerializer.serialize = safe_serialize


# 📊 Plot Collector
from src.dataframe_analyzers.pd_df_agent.plot_collector import PlotCollector

collector = PlotCollector(output_dir="charts", save=True)
collector.patch_matplotlib()


# 🪵 LOGS
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# 🔑 ENV
load_dotenv()


# 🤖 LLM
llm = OpenAI(
    temperature=0,
    max_tokens=1000
)


# 📂 LOAD DATA
with open("src\\agents\\sheet_analyzer\\sheets\\ENQUETE_OTB_ACAOPROMO.xlsx", "rb") as f:
    file_bytes = f.read()

df = pd.read_excel(BytesIO(file_bytes))


# 🧠 AGENT
agent = Agent(
    df,
    config={
        "llm": llm,
        "verbose": True,
        "save_logs": True,
        "max_retries": 3,
        "temperature": 0,
        "enable_cache": False,
    },
    memory_size=5,
    description="""
    You are a senior data analyst.

    RULES:
    - Always validate calculations before answering
    - Prefer structured outputs
    - Never hallucinate data
    - Keep answers concise

    CRITICAL:
    - When generating charts, ALWAYS use matplotlib
    - ALWAYS call plt.show()
    - DO NOT rely on file paths for charts
    """
)


# 🧠 FUNÇÃO PRINCIPAL
def ask_agent(question: str):
    print(f"\nPergunta: {question}")

    # 🔄 reseta gráficos
    collector.reset()

    result = None

    try:
        result = agent.chat(question)

    except Exception as e:
        print("\n⚠️ Erro tratado:", e)

    # 📊 coleta gráficos SEMPRE
    graphs = collector.get_graphs()

    # 🧠 fallback inteligente
    if (not result or "Unfortunately" in str(result)) and graphs:
        result = "Claro! Gere um gráfico com base na sua solicitação."

    # 🔍 DEBUG
    if hasattr(agent, "last_code_generated"):
        print("\n🧾 Código gerado:")
        print(agent.last_code_generated)

    print("\n✅ Resultado:")
    print(result)

    print(f"\n📊 Gráficos gerados: {len(graphs)}")

    return {
        "result": result,
        "graphs": graphs
    }


# 🏃 LOOP INTERATIVO
if __name__ == "__main__":
    while True:
        q = input("\nDigite sua pergunta (ou 'sair'): ")

        if q.lower() == "sair":
            break

        ask_agent(q)

# Gere um grafico de barras da média de idade por genero
# python -m src.dataframe_analyzers.pandas_ai.test3