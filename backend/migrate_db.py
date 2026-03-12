import sqlite3
import os

def migrate():
    db_file = 'pdp_academy.db'
    if not os.path.exists(db_file):
        print(f"Error: {db_file} not found")
        return

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # 1. Add missing columns to 'users' table
    columns_to_add = [
        ("phone", "VARCHAR(50)"),
        ("address", "TEXT"),
        ("avatar_url", "VARCHAR(500)"),
        ("gender", "VARCHAR(10)"),
        ("birth_date", "DATETIME"),
        ("nationality", "VARCHAR(100)"),
        ("passport_id", "VARCHAR(50)")
    ]

    cursor.execute("PRAGMA table_info(users)")
    existing_cols = [c[1] for c in cursor.fetchall()]

    for col_name, col_type in columns_to_add:
        if col_name not in existing_cols:
            print(f"Adding column {col_name} to users table...")
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"Error adding {col_name}: {e}")

    # 2. Ensure 'timetable' table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='timetable';")
    if not cursor.fetchone():
        print("Creating table 'timetable'...")
        cursor.execute("""
            CREATE TABLE timetable (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                day_of_week VARCHAR(20) NOT NULL,
                lesson_number INTEGER NOT NULL,
                start_time VARCHAR(10) NOT NULL,
                end_time VARCHAR(10) NOT NULL,
                room VARCHAR(50) NOT NULL,
                subject VARCHAR(255) NOT NULL,
                FOREIGN KEY(teacher_id) REFERENCES teachers(id),
                FOREIGN KEY(group_id) REFERENCES groups(id)
            )
        """)

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
