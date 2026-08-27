"""
Script Seeder untuk membuat akun awal Super Admin dan Admin di Database Backend
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import Base, SessionLocal, engine
from app.core.security import get_password_hash
from app.models.user import User


def seed_initial_users():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Super Admin
        super_admin_email = "superadmin@satubumi.org"
        existing_super = db.query(User).filter(User.email == super_admin_email).first()
        if not existing_super:
            super_user = User(
                email=super_admin_email,
                hashed_password=get_password_hash("superadmin123"),
                full_name="Super Administrator",
                role="super_admin",
                is_active=True,
            )
            db.add(super_user)
            print(
                f"[OK] Akun Super Admin berhasil dibuat: {super_admin_email} / superadmin123"
            )
        else:
            existing_super.role = "super_admin"
            db.commit()
            print(f"[INFO] Akun Super Admin sudah ada: {super_admin_email}")

        # 2. Content Admin
        admin_email = "admin@satubumi.org"
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        if not existing_admin:
            admin_user = User(
                email=admin_email,
                hashed_password=get_password_hash("admin123"),
                full_name="Content Admin",
                role="admin",
                is_active=True,
            )
            db.add(admin_user)
            print(f"[OK] Akun Admin berhasil dibuat: {admin_email} / admin123")
        else:
            existing_admin.role = "admin"
            db.commit()
            print(f"[INFO] Akun Admin sudah ada: {admin_email}")

        db.commit()
        print("\n[OK] Seeding akun admin selesai!")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error seeding database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_initial_users()
