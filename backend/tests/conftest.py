"""
Shared test infrastructure.

IMPORTANT: test_auth.py and test_farmer.py both install dependency_overrides
on the FastAPI app singleton. To prevent them clobbering each other when pytest
collects all modules, this conftest provides a single shared SQLite+StaticPool
engine and a module-scoped app-override fixture.

Tests that need the TestClient directly (test_database.py) continue to use
the session-scoped `engine` + `db` fixtures for raw ORM access.
"""

import pytest
from sqlalchemy import create_engine, event, StaticPool
from sqlalchemy.orm import sessionmaker, Session

# Import all models so Base.metadata is fully populated
import app.models  # noqa: F401
from app.database.base import Base
from app.database.session import get_db
from app.main import app as fastapi_app

# ── Single shared engine used by ALL test modules ─────────────────────────────

_SHARED_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)


@event.listens_for(_SHARED_ENGINE, "connect")
def _fk_pragma(dbapi_conn, _):
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA foreign_keys=ON")
    cur.close()


Base.metadata.create_all(_SHARED_ENGINE)

_SharedSession = sessionmaker(bind=_SHARED_ENGINE, autocommit=False, autoflush=False)


def _override_get_db():
    db = _SharedSession()
    try:
        yield db
    finally:
        db.close()


# Install the override once at import time — all test modules share this
fastapi_app.dependency_overrides[get_db] = _override_get_db


# ── Expose for test files that need direct DB access ──────────────────────────

def get_test_session() -> Session:
    """Return a raw session on the shared test engine (caller must close)."""
    return _SharedSession()


# ── Fixtures for test_database.py (raw ORM, no HTTP client) ──────────────────

@pytest.fixture(scope="session")
def engine():
    """The shared in-memory engine (session-scoped)."""
    return _SHARED_ENGINE


@pytest.fixture
def db(engine) -> Session:
    """Function-scoped session that rolls back after every test."""
    connection = engine.connect()
    transaction = connection.begin()
    _Sess = sessionmaker(bind=connection, autocommit=False, autoflush=False)
    session = _Sess()
    yield session
    session.close()
    transaction.rollback()
    connection.close()
