import os
from dotenv import load_dotenv

from agno.db.sqlite import SqliteDb
from agno.db.postgres import PostgresDb

load_dotenv()


class Database:
    def __new__(
        cls,
        local: bool = False,
        database_name: str | None = None,
        database_url: str | None = None,
    ):
        if local:
            return cls._local_database(database_name)
        return cls._supabase(database_url)

    @staticmethod
    def _get_database_name(database_name: str | None):
        path = "src/agents/database"
        if database_name:
            return f"{path}/{database_name}.db"
        return f"{path}/agno.db"

    @staticmethod
    def _get_database_url(database_url: str | None):
        if database_url:
            return database_url
        
        host = os.getenv("SUPABASE_PROJECT_HOST")
        password = os.getenv("SUPABASE_DATABASE_PASSWORD")

        return f"postgresql://postgres:{password}@db.{host}:5432/postgres"

    @classmethod
    def _supabase(cls, database_url: str | None):
        return PostgresDb(
            db_schema="agent_db",
            db_url=cls._get_database_url(database_url),

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

    @classmethod
    def _local_database(cls, database_name: str | None):
        return SqliteDb(
            db_file=cls._get_database_name(database_name),

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