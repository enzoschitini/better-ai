from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.openai import OpenAIChat
from dotenv import load_dotenv

load_dotenv()

SUPABASE_DB_URL = SUPABASE_DB_DIRECT_URL

db = PostgresDb(db_url=SUPABASE_DB_URL)

agent = Agent(
    id="test-agent",
    session_id="session_1",
    user_id="enzo",
    model=OpenAIChat(id="gpt-4.1-mini"),
    db=db
)
response = agent.run("Ciao! Come vanno le cose?")

print(response.content)

