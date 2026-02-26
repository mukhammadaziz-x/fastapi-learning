import psycopg2
import sys

try:
    conn = psycopg2.connect(
        dbname="fastapi",
        user="postgres",
        password="1111111",
        host="localhost",
        port="5432",
    )
    print("DB connected successfully!")
    conn.close()
except Exception as e:
    print(f"DB connection FAILED: {e}", file=sys.stderr)
    sys.exit(1)

