import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

"""
conn = psycopg2.connect(os.getenv("SUPABASE_DATABASE_URL"))
print("Conectado com sucesso ao pooler!")
conn.close()
"""

import os
import psycopg2
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


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

    def get_db_connection(self):
        """Retorna conexão PostgreSQL (lazy)."""
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(self.db_url)

            # importante para transações controladas
            self._conn.autocommit = False

        return self._conn

    def close(self):
        """Fecha a conexão com o banco."""
        if self._conn and not self._conn.closed:
            self._conn.close()
            self._conn = None

supabase_connection = SupabaseConnection()

conn = supabase_connection.get_db_connection()
print("Conectado!")

supabase_connection.close()
