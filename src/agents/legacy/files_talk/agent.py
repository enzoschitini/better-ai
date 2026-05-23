import os
import json

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from agents.legacy.files_talk.toolkit import RetrievalAugmentedGeneration
from agents.legacy.files_talk.config import PROMPT, DEFAULT_MODEL

from src.agents.utils.database import Database
from src.agents.utils.agno_ai_agents import BaseAgent, ToolContext

from dotenv import load_dotenv

load_dotenv()

class FileTalkAgent(BaseAgent):
    def _validate_metadata(self, metadata: dict):
        if "session_id" not in metadata:
            raise ValueError("metadata must contain 'session_id'")

        if "user_id" not in metadata:
            raise ValueError("metadata must contain 'user_id'")

    def create_agent(self, metadata: dict, tool_context: ToolContext):
        self._validate_metadata(metadata)
        db = Database(local=True, local_path="src/agents/files_talk/data")

        return Agent(
            id="files_talk_agent",
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
                RetrievalAugmentedGeneration(
                    TOOL_RESPONSER=tool_context.tool_responser,
                    filter_search=metadata["filter_search"]
                )
            ],
        )

# python -m src.agents.files_talk.agent