import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_experimental.agents import create_pandas_dataframe_agent

from dotenv import load_dotenv

load_dotenv()

# 🔥 Carregar CSV
df = pd.read_csv("src/agents/sheet_analyzer/doc/supermarket_sales.csv")

# 🔥 LLM
llm = ChatOpenAI(
    model="gpt-4.1",
    temperature=0
)

# 🔥 Criar agente
agent = create_pandas_dataframe_agent(
    llm,
    df,
    verbose=True,
    allow_dangerous_code=True
)

# 🔥 Pergunta
resposta = agent.invoke("Qual produto teve mais vendas?")
print(resposta)