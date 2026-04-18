from dotenv import load_dotenv

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from src.agents.sheet_analyzer.toolkit import DataframeAnalyzer
from src.agents.sheet_analyzer.config import DEFAULT_MODEL, PROMPT
from src.agents.agno_ai_agents.agents import BaseAgent, ToolContext

load_dotenv()

class DataframeAgent(BaseAgent):

    def _validate_metadata(self, metadata: dict):
        if "dataframe" not in metadata:
            raise ValueError("metadata deve conter 'dataframe'")

    def create_agent(self, metadata: dict, tool_context: ToolContext):
        self._validate_metadata(metadata)

        return Agent(
            id="sheet_analyzer",
            model=OpenAIChat(id=DEFAULT_MODEL),
            instructions=PROMPT["instructions"],
            description=PROMPT["description"],
            markdown=True,
            stream=True,
            debug_level=True,
            tools=[
                DataframeAnalyzer(
                    TOOL_RESPONSER=tool_context.tool_responser,
                    dataframe=metadata["dataframe"]
                )
            ],
        )

# python -m src.agents.sheet_analyzer.agent