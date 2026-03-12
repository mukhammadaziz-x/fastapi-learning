import sqlite3
import os

def check_tables():
    db_file = 'pdp_academy.db'
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", [t[0] for t in tables])
    
    cursor.execute("PRAGMA table_info(users)")
    print("Users columns:", [c[1] for c in cursor.fetchall()])
    conn.close()

if __name__ == "__main__":
    check_tables()
