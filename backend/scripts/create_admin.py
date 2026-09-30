"""
Create a development admin account if one does not exist.
Reads credentials from environment variables.

Usage:
    cd backend
    .venv\\Scripts\\python.exe scripts/create_admin.py
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from app.database.session import SessionLocal
from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User, UserRole


def create_admin() -> None:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
        if existing:
            print(f"[admin] Account already exists: {settings.ADMIN_EMAIL}")
            return

        admin = User(
            full_name="Administrator",
            email=settings.ADMIN_EMAIL,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"[admin] Created admin account: {settings.ADMIN_EMAIL}")
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
