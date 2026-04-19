import json
import pandas as pd
from io import BytesIO

from src.agents.utils.agno_ai_agents import AgnoAiAgents
from src.agents.sheet_analyzer.agent import DataframeAgent
from src.agents.utils.test_agents.run_agent import RunAgent


if __name__ == "__main__":
    # =========================
    # LOAD DATA
    # =========================
    with open("src/dataframe_analyzers/pd_df_agent/test/supermarket_sales.csv", "rb") as f:
        df = pd.read_csv(BytesIO(f.read()))

    # =========================
    # FACTORY
    # =========================
    agno = AgnoAiAgents()
    agno.register("DataframeAgent", DataframeAgent)

    # =========================
    # CREATE
    # =========================
    agent, tool_context = agno.create_agent(
        "DataframeAgent",
        {
            "session_id": "12345",
            "user_id": "user_01",
            "dataframe": df
        }
    )

    # =========================
    # RUN
    # =========================
    runner = RunAgent(agent=agent)
    runner.debug(ask="Qual a proporção de homens e mulheres?")
    #runner.agent_os()

    # =========================
    # TOOL METADATA
    # =========================
    print("\nTool Response Metadata:")
    print(json.dumps(tool_context.tool_responser.get_metadata(), indent=4))

# python -m src.agents.sheet_analyzer.run
