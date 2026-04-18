import os
from dotenv import load_dotenv

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from src.agents.ultils.tool_response import ToolResponse
from src.agents.sheet_analyzer.toolkit import DataframeAnalyzer
from src.agents.sheet_analyzer.config import DEFAULT_MODEL, PROMPT

load_dotenv()


# =========================================================
# TOOL RESPONDER (COMPARTILHADO)
# =========================================================
class ToolContext:
    def __init__(self):
        self.tool_responser = ToolResponse()


# =========================================================
# BASE AGENT (CONTRATO)
# =========================================================
class BaseAgent:
    def create_agent(self, metadata: dict, context: ToolContext):
        raise NotImplementedError


# =========================================================
# DATAFRAME AGENT
# =========================================================
class DataframeAgent(BaseAgent):

    def _validate_metadata(self, metadata: dict):
        if not isinstance(metadata, dict):
            raise ValueError("metadata deve ser um dict")

        if "dataframe" not in metadata:
            raise ValueError("metadata deve conter 'dataframe'")

    def create_agent(self, metadata: dict, context: ToolContext):
        self._validate_metadata(metadata)

        dataframe = metadata["dataframe"]

        agent = Agent(
            id="sheet_analyzer",

            # =========================
            # SETTINGS
            # =========================
            model=OpenAIChat(id=DEFAULT_MODEL),
            instructions=PROMPT["instructions"],
            description=PROMPT["description"],

            markdown=True,
            stream=True,
            debug_level=True,

            # =========================
            # TOOLS
            # =========================
            tools=[
                DataframeAnalyzer(
                    TOOL_RESPONSER=context.tool_responser,
                    dataframe=dataframe  # 🔥 PADRONIZADO
                )
            ],
        )

        return agent


# =========================================================
# AGENT FACTORY (ORQUESTRADOR)
# =========================================================
class AgnoAiAgents:

    def __init__(self):
        self._registry = {
            "DataframeAgent": DataframeAgent,
        }

    def create_agent(self, id: str, metadata: dict):
        if id not in self._registry:
            raise ValueError(f"Agent '{id}' não registrado.")

        context = ToolContext()

        agent_class = self._registry[id]
        agent_instance = agent_class()

        agent = agent_instance.create_agent(metadata, context)

        return agent, context


# =========================================================
# EXECUÇÃO
# =========================================================
if __name__ == "__main__":
    import json
    import pandas as pd
    from io import BytesIO

    from src.agents.ultils.test_agents.run_agent import RunAgent

    # =========================
    # LOAD DATAFRAME
    # =========================
    with open("src/dataframe_analyzers/pd_df_agent/test/supermarket_sales.csv", "rb") as f:
        file_bytes = f.read()

    df = pd.read_csv(BytesIO(file_bytes))

    # =========================
    # FACTORY
    # =========================
    agno = AgnoAiAgents()

    agent, context = agno.create_agent(
        id="DataframeAgent",
        metadata={
            "dataframe": df
        }
    )

    # =========================
    # RUNNER
    # =========================
    runner = RunAgent(agent=agent)

    ASK = "Qual a média de preço?"

    runner.debug(ask=ASK)

    # =========================
    # TOOL METADATA
    # =========================
    print("\nTool Response Metadata:")
    print(json.dumps(context.tool_responser.get_metadata(), indent=4))

# python -m src.agents.sheet_analyzer.agent