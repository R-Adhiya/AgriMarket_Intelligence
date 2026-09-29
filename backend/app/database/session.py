"""
Database configuration for AgriMarket Intelligence.

Phase 1: Architecture placeholder — no tables created yet.
Phase 2: PostgreSQL + SQLAlchemy integration will be implemented here.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Engine — not used in Phase 1, instantiated here for architecture completeness
# The connection will only be established when explicitly called
engine = None  # Will be: create_engine(settings.DATABASE_URL)

# Session factory — Phase 2+
SessionLocal = None

# Base class for all ORM models — Phase 2+
Base = declarative_base()


def get_db():
    """
    Dependency for FastAPI route handlers.
    Yields a database session and ensures it is closed after the request.
    Phase 2+: Uncomment the implementation below.
    """
    # db = SessionLocal()
    # try:
    #     yield db
    # finally:
    #     db.close()
    pass  # Phase 1 placeholder
