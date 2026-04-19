import os
from dotenv import load_dotenv

from agno.db.sqlite import SqliteDb
from agno.db.postgres import PostgresDb

load_dotenv()


class Database:
    """
    Database is a factory class that provides an interface to connect either 
    to a local SQLite database or a Supabase Postgres database depending on the parameters.
    It abstracts the database connection logic and configuration details.

    Args:
        local (bool): If True, connects to a local SQLite database, default is False.
        database_name (str | None): The name of the database or schema to connect to, default is None.
        database_url (str | None): The full URL for the remote database connection, default is None.

    Methods:
        None (all accessible functionality is through __new__ and internal methods)
    """
    def __new__(
        cls,
        local: bool = False,
        database_name: str | None = None,
        database_url: str | None = None,
    ):
        if local:
            return cls._local_database(database_name)
        return cls._supabase(database_url, database_name)

    @staticmethod
    def _get_schema_name(database_name: str | None):
        """
        Returns the schema name for the database connection. 
        Defaults to 'agent_db' if no database_name is provided.

        Args:
            database_name (str | None): The database schema name, default is None.

        Returns:
            str: The schema name to be used.
        """
        if database_name:
            return database_name
        return "agent_db"

    @staticmethod
    def _get_database_local_storage(database_name: str | None):
        """
        Constructs the local SQLite database file path based on the database name.
        Defaults to 'src/agents/database/agno.db' if no database_name is provided.

        Args:
            database_name (str | None): The local database file name, default is None.

        Returns:
            str: The full path to the local SQLite database file.
        """
        path = "src/agents/database"
        if database_name:
            return f"{path}/{database_name}.db"
        return f"{path}/agno.db"

    @staticmethod
    def _get_database_url(database_url: str | None):
        """
        Determines the database URL to use for the Supabase Postgres connection. 
        If a URL is provided, it returns it directly; otherwise constructs one using environment variables.

        Args:
            database_url (str | None): Optional full database URL, default is None.

        Returns:
            str: The Postgres database URL.
        """
        if database_url:
            return database_url
        
        host = os.getenv("SUPABASE_PROJECT_HOST")
        password = os.getenv("SUPABASE_DATABASE_PASSWORD")

        return f"postgresql://postgres:{password}@db.{host}:5432/postgres"

    @classmethod
    def _supabase(cls, database_url: str | None, database_name: str | None):
        """
        Creates and returns a PostgresDb instance configured for the Supabase database,
        using the specified database URL and schema name.

        Args:
            database_url (str | None): The database URL to connect to, default is None.
            database_name (str | None): The schema name for the database, default is None.

        Returns:
            PostgresDb: An instance of PostgresDb configured for Supabase.
        """
        return PostgresDb(
            db_schema=cls._get_schema_name(database_name),
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
        """
        Creates and returns a SqliteDb instance configured for local file storage,
        using the specified database name to determine the file path.

        Args:
            database_name (str | None): The name of the local database file, default is None.

        Returns:
            SqliteDb: An instance of SqliteDb configured for local use.
        """
        return SqliteDb(
            db_file=cls._get_database_local_storage(database_name),

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