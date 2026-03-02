"""Fix NULL created_at/updated_at in existing records."""
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    db.execute(text("UPDATE tests SET created_at = NOW(), updated_at = NOW() WHERE created_at IS NULL"))
    db.execute(text("UPDATE questions SET created_at = NOW() WHERE created_at IS NULL"))
    db.execute(text("UPDATE teachers SET created_at = NOW() WHERE created_at IS NULL"))
    db.execute(text("UPDATE students SET created_at = NOW() WHERE created_at IS NULL"))
    db.commit()
    print("All NULL dates fixed successfully!")
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
