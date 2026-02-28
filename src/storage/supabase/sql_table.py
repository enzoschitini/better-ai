import os
from psycopg2.extras import RealDictCursor
from typing import Optional, List, Dict, Any
import psycopg2
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


class SupabaseConnection:
    """Gerencia conexões com Supabase (API + PostgreSQL)."""

    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SECRET_KEY")

        # DB
        self.db_host = os.getenv("SUPABASE_DB_HOST")
        self.db_name = os.getenv("SUPABASE_DB_NAME")
        self.db_user = os.getenv("SUPABASE_DB_USER")
        self.db_password = os.getenv("SUPABASE_DB_PASSWORD")
        self.db_port = os.getenv("SUPABASE_DB_PORT", 5432)

        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL e SUPABASE_SECRET_KEY são obrigatórias.")

        self.client: Client = create_client(self.url, self.key)

        self._conn = None

    def get_db_connection(self):
        """Retorna conexão PostgreSQL (lazy)."""
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(
                host=self.db_host,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
                port=self.db_port
            )
            self._conn.autocommit = False

        return self._conn

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()

supabase_client = SupabaseConnection()
print(supabase_client)


class SupabaseQueryEngineer:
    """Responsável apenas por executar queries."""

    def __init__(self, connection):
        self.connection = connection

    def _execute(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch: bool = False
    ) -> Optional[List[Dict[str, Any]]]:

        conn = self.connection.get_db_connection()

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)

                result = cursor.fetchall() if fetch else None

                conn.commit()
                return result

        except Exception as e:
            conn.rollback()
            raise Exception(f"Erro ao executar query: {str(e)}")

    # =====================
    # PUBLIC METHODS
    # =====================

    def select(self, query: str, params: Optional[tuple] = None):
        return self._execute(query, params, fetch=True)

    def execute(self, query: str, params: Optional[tuple] = None):
        self._execute(query, params, fetch=False)

    def execute_many(self, query: str, params_list: List[tuple]):
        conn = self.connection.get_db_connection()

        try:
            with conn.cursor() as cursor:
                cursor.executemany(query, params_list)
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"Erro ao executar múltiplas queries: {str(e)}")

connection = SupabaseConnection()
query_engine = SupabaseQueryEngineer(connection)

query_engine.execute("""
create table if not exists users_app (
    id uuid primary key default gen_random_uuid(),
    name text,
    data jsonb
);
""")

# python -m src.storage.supabase.sql_table