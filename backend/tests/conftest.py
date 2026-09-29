"""
Shared pytest fixtures.

The test database uses SQLite in-memory so no PostgreSQL instance is required.
SQLAlchemy maps all our PostgreSQL types to SQLite equivalents automatically,
with one exception: Enum types with `create_type=False` are fine; CHECK
constraints are supported from SQLite 3.25+.
"""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from app.database.base import Base

# ── Import all models so Base.metadata is populated ───────────────────────────
import app.models  # noqa: F401


TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    """Session-scoped SQLite in-memory engine."""
    _engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    # Enable foreign-key enforcement in SQLite
    @event.listens_for(_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(_engine)
    yield _engine
    Base.metadata.drop_all(_engine)
    _engine.dispose()


@pytest.fixture
def db(engine) -> Session:
    """Function-scoped session that rolls back after every test."""
    connection = engine.connect()
    transaction = connection.begin()
    _Session = sessionmaker(bind=connection, autocommit=False, autoflush=False)
    session = _Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()
