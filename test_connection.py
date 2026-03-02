"""Test PostgreSQL connection."""
import sys

try:
    from app.database import engine
    with engine.connect() as conn:
        result = conn.execute(__import__('sqlalchemy').text("SELECT 1"))
        print("✅ PostgreSQL connection successful!")
        print(f"   Result: {result.fetchone()}")
except Exception as e:
    print(f"❌ PostgreSQL connection failed: {e}", file=sys.stderr)
    print("   Make sure PostgreSQL is running and database 'fastapi' exists.")
    print(f"   Error type: {type(e).__name__}")

