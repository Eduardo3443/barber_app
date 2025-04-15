import sqlite3

def create_db():
    conn = sqlite3.connect('barber.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            visits INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()
