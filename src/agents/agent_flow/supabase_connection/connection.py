from agno.agent import Agent
from agno.db.postgres import PostgresDb
from src.database.relational_db.supabase_database import SupabaseConnection, SupabaseQueryEngineer

from agno.agent import Agent
from agno.db.postgres import PostgresDb

def agno():
    # Get your Supabase project and password
    SUPABASE_PROJECT = "019c4370-8220-74ee-9e66-42aeafbb9e76"
    SUPABASE_PASSWORD = "hsenyunovbrmjejxqvjn.supabase.co"

    SUPABASE_DB_URL = (
        f"postgresql://postgres:{SUPABASE_PROJECT}@db.{SUPABASE_PASSWORD}:5432/postgres"
    )

    # Setup the Supabase database
    db = PostgresDb(db_url=SUPABASE_DB_URL)

    # Setup your Agent with the Database
    agent = Agent(db=db)


def agno2():
    # Get your Supabase project and password
    SUPABASE_PROJECT = "019c4370-8220-74ee-9e66-42aeafbb9e76"
    SUPABASE_PASSWORD = "hsenyunovbrmjejxqvjn.supabase.co"

    SUPABASE_DB_URL = (
        f"postgresql://postgres:{SUPABASE_PASSWORD}@db.{SUPABASE_PROJECT}:5432/postgres"
    )

    # Setup the Supabase database
    db = PostgresDb(db_url=SUPABASE_DB_URL)

    # Setup your Agent with the Database
    agent = Agent(db=db)

def supabase():
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
    # CLEANUP
    # =====================

    connection.close()

agno2()

# python -m src.agents.agent_flow.supabase_connection.connection