import os
from typing import Optional, List, Dict, Any, Callable

import psycopg2
from psycopg2.extras import RealDictCursor
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


# ================================
# CONNECTION LAYER
# ================================

class SupabaseConnection:
    """Gerencia conexões com Supabase (API + PostgreSQL via pooler)."""

    def __init__(self):
        # API
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SECRET_KEY")

        # DB (pooler URL)
        self.db_url = os.getenv("SUPABASE_DATABASE_URL")

        # validações
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL e SUPABASE_SECRET_KEY são obrigatórias.")

        if not self.db_url:
            raise ValueError("SUPABASE_DATABASE_URL é obrigatória.")

        # cliente supabase (REST)
        self.client: Client = create_client(self.url, self.key)

        # conexão postgres
        self._conn = None

    def get_connection(self):
        """Retorna conexão PostgreSQL (lazy + auto-reconnect)."""
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(self.db_url)
            self._conn.autocommit = False
        else:
            # ping para evitar conexão morta
            try:
                with self._conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
            except Exception:
                self._conn = psycopg2.connect(self.db_url)
                self._conn.autocommit = False

        return self._conn

    def close(self):
        """Fecha a conexão com o banco."""
        if self._conn and not self._conn.closed:
            self._conn.close()
            self._conn = None


# ================================
# QUERY ENGINE
# ================================

class SupabaseQueryEngineer:
    """Responsável apenas por executar queries SQL."""

    def __init__(self, get_connection: Callable):
        """
        get_connection: função que retorna uma conexão ativa
        """
        self.get_connection = get_connection

    def _execute(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch: bool = False
    ) -> Optional[List[Dict[str, Any]]]:

        conn = self.get_connection()

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
        conn = self.get_connection()

        try:
            with conn.cursor() as cursor:
                cursor.executemany(query, params_list)
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"Erro ao executar múltiplas queries: {str(e)}")


# ================================
# USAGE EXAMPLE
# ================================

if __name__ == "__main__":
    # cria conexão
    connection = SupabaseConnection()

    # injeta apenas o método de conexão (baixo acoplamento)
    query_engine = SupabaseQueryEngineer(connection.get_connection)

    print("Conectado!")

    # =====================
    # CREATE TABLE
    # =====================

    query_engine.execute("""
    create extension if not exists pgcrypto;
    """)

    query_engine.execute("""
    create table if not exists users_app (
        id uuid primary key default gen_random_uuid(),
        name text,
        data jsonb,
        created_at timestamp default now()
    );
    """)

    # =====================
    # INSERT
    # =====================

    query_engine.execute(
        "insert into users_app (name, data) values (%s, %s)",
        ("Enzo", '{"age": 25}')
    )

    # =====================
    # SELECT
    # =====================

    users = query_engine.select("select * from users_app")

    print("Users:")
    for user in users:
        print(user)

    # =====================
    # CLEANUP
    # =====================

    connection.close()