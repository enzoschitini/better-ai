import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

engine = create_engine(os.getenv("SUPABASE_DATABASE_URL"))

with engine.connect() as conn:
    result = conn.execute(text("SELECT NOW()"))
    print(result.fetchone())

import sqlite3

conn = sqlite3.connect("src/agents/agent_flow/agno.db")

cursor = conn.cursor()

cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")

tables = cursor.fetchall()

for table in tables:
    if table[0] is not None:
        print(table[0] + ";\n")