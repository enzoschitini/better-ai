import os
from dotenv import load_dotenv

from agno.db.sqlite import SqliteDb
from agno.db.postgres import PostgresDb

from src.agents.rag_agent.config import LOCAL_MEMORY_DB

load_dotenv()

class Database:
    def __new__(cls, local: bool = False):
        if local:
            return cls.local_database()
        return cls.supabase()

    @staticmethod
    def supabase():
        SUPABASE_PROJECT_HOST = os.getenv("SUPABASE_PROJECT_HOST")
        SUPABASE_DATABASE_PASSWORD = os.getenv("SUPABASE_DATABASE_PASSWORD")

        SUPABASE_DB_URL = (
            f"postgresql://postgres:{SUPABASE_DATABASE_PASSWORD}@db.{SUPABASE_PROJECT_HOST}:5432/postgres"
        )

        return PostgresDb(
            db_url=SUPABASE_DB_URL,

            session_table="sessions",
            memory_table="memories",
            metrics_table="metrics",
            eval_table="eval_runs",
            knowledge_table="knowledge",
            culture_table="culture",
            traces_table="traces",
            spans_table="spans",
            versions_table="schema_versions",
            components_table="components",
            component_configs_table="component_configs",
            component_links_table="component_links",
            learnings_table="learnings",
            schedules_table="schedules",
            schedule_runs_table="schedule_runs",
            approvals_table="approvals",
        )

    @staticmethod
    def local_database():
        return SqliteDb(
            db_file=LOCAL_MEMORY_DB,

            session_table="sessions",
            memory_table="memories",
            metrics_table="metrics",
            eval_table="eval_runs",
            knowledge_table="knowledge",
            culture_table="culture",
            traces_table="traces",
            spans_table="spans",
            versions_table="schema_versions",
            components_table="components",
            component_configs_table="component_configs",
            component_links_table="component_links",
            learnings_table="learnings",
            schedules_table="schedules",
            schedule_runs_table="schedule_runs",
            approvals_table="approvals",
        )

