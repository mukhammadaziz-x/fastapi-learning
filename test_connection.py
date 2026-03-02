import sys
import os
os.environ["PYTHONIOENCODING"] = "utf-8"

try:
    from app.database import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        row = result.fetchone()
        print("SUCCESS: PostgreSQL connection OK. Result: " + str(row))
except Exception as e:
    print("FAIL: " + str(type(e).__name__) + ": " + str(e))
    sys.exit(1)

