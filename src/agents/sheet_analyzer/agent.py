from dotenv import load_dotenv

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from src.agents.ultils.database import Database
from src.agents.sheet_analyzer.toolkit import DataframeAnalyzer
from src.agents.sheet_analyzer.config import DEFAULT_MODEL, PROMPT
from src.agents.agno_ai_agents.agents import BaseAgent, ToolContext

load_dotenv()

class DataframeAgent(BaseAgent):

    def _validate_metadata(self, metadata: dict):
        if "session_id" not in metadata:
            raise ValueError("metadata must contain 'session_id'")

        if "user_id" not in metadata:
            raise ValueError("metadata must contain 'user_id'")

        if "dataframe" not in metadata:
            raise ValueError("metadata must contain 'dataframe'")

    def create_agent(self, metadata: dict, tool_context: ToolContext):
        self._validate_metadata(metadata)
        db = Database(local=True)

        return Agent(
            id="sheet_analyzer",
            session_id=metadata.get("session_id", "default_session"),
            user_id=metadata.get("user_id", "default_user"),

            model=OpenAIChat(id=DEFAULT_MODEL),

            instructions=PROMPT["instructions"],
            description=PROMPT["description"],
            markdown=True,

            db=db,
            add_history_to_context=True,
            num_history_runs=10,
            enable_user_memories=True,
            add_memories_to_context=True,

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