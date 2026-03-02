"""Admin user yaratish skripti."""
from app.database import SessionLocal
from app.crud.user import create_user_from_register, get_user_by_email

def main():
    db = SessionLocal()
    try:
        # Tekshirish
        existing = get_user_by_email(db, "admin@eduplatform.uz")
        if existing:
            print(f"Admin allaqachon mavjud: {existing.username}")
            return

        # Admin yaratish
        admin = create_user_from_register(
            db,
            email="admin@eduplatform.uz",
            username="admin",
            password="admin123",
            full_name="Platform Admin",
            role="admin",
        )
        print("=" * 45)
        print("  ADMIN USER YARATILDI!")
        print("=" * 45)
        print(f"  Email:    admin@eduplatform.uz")
        print(f"  Username: admin")
        print(f"  Password: admin123")
        print(f"  Role:     admin")
        print("=" * 45)

    finally:
        db.close()

if __name__ == "__main__":
    main()
