import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv("SUPABASE_DATABASE_URL"))
print("Conectado com sucesso ao pooler!")
conn.close()