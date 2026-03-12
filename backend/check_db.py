import sqlite3
import os

def check_schema():
    db_file = 'pdp_academy.db'
    if not os.path.exists(db_file):
        print(f"File {db_file} not found")
        return
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    cols = cursor.fetchall()
    for col in cols:
        print(col)
    conn.close()

if __name__ == "__main__":
    check_schema()
