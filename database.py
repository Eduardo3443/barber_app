import psycopg2
import os
from urllib.parse import urlparse

def create_db():
    # Usa DATABASE_URL desde las variables de entorno (Render la configura sola)
    DATABASE_URL = os.environ.get("DATABASE_URL")

    if not DATABASE_URL:
        raise ValueError("DATABASE_URL no está configurada")

    # Parsea la URL si tiene formato postgres:// y lo convierte a postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # Conexión a PostgreSQL
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            visits INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()
