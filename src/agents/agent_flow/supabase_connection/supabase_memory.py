from agno.agent import Agent
from agno.os import AgentOS
from agno.models.openai import OpenAIChat
from agno.db.postgres import PostgresDb
import os
from dotenv import load_dotenv
from src.agents.ultils.run_agent import RunAgent

load_dotenv()

db = PostgresDb(db_url=os.getenv("SUPABASE_DATABASE_URL"))

agent = Agent(
    id="test-agent",
    model=OpenAIChat(id="gpt-4.1-mini"),
    db=db,
    add_history_to_context=True,
    num_history_runs=10,
    enable_user_memories=True,
    add_memories_to_context=True,
)

runner = RunAgent(agent=agent)
runner.agent_os()

# python -m src.agents.agent_flow.supabase_memory