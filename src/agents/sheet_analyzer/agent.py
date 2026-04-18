import os
from dotenv import load_dotenv

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from src.agents.ultils.tool_response import ToolResponse
from src.agents.sheet_analyzer.toolkit import DataframeAnalyzer
from src.agents.sheet_analyzer.config import DEFAULT_MODEL, PROMPT, LOCAL_MEMORY_DB

load_dotenv()

TOOL_RESPONSER = ToolResponse()

def create_agent(df):
    agent = Agent(
        id="sheet_analyzer",

        # Settings
        model=OpenAIChat(id=DEFAULT_MODEL), 
        instructions=PROMPT["instructions"],
        description=PROMPT["description"],
        markdown=True,
        stream=True,
        debug_level=True,

        # Toolkit
        tools=[
            DataframeAnalyzer(TOOL_RESPONSER=TOOL_RESPONSER, df=df)
        ],
    )

    return agent

if __name__ == "__main__":
    import json
    import pandas as pd
    from io import BytesIO

    from src.agents.ultils.test_agents.run_agent import RunAgent

    with open("src/dataframe_analyzers/pd_df_agent/test/supermarket_sales.csv", "rb") as f:
        file_bytes = f.read()

    df = pd.read_csv(BytesIO(file_bytes))
    agent = create_agent(df)

    runner = RunAgent(agent=agent)
    ASK = """
Qual a média de preço?
"""
    #runner.process(ask=ASK, tool_responses=response_collector)
    runner.debug(ask=ASK)
    #runner.agent_os()

    print("Tool Response Metadata:")
    print(json.dumps(TOOL_RESPONSER.get_metadata(), indent=4))

# python -m src.agents.sheet_analyzer.agent