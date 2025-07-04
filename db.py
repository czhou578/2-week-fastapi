import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

def create_table():
    cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

create_table()
conn.close()