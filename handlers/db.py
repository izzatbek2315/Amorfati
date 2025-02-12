import sqlite3
import os
db_path = 'users.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path, check_same_thread=False)
else:
    conn = sqlite3.connect(db_path, check_same_thread=False)

cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        chat_id INTEGER PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        username TEXT       
    )
''')
conn.commit()

