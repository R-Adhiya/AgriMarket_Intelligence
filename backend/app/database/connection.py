"""
SQLAlchemy engine and connection-pool configuration.
Reads DATABASE_URL from the environment via app.core.config.

Supports both PostgreSQL (production) and SQLite (development/testing).
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import OperationalError

from app.core.config import settings

_url = settings.DATABASE_URL
_is_sqlite = _url.startswith("sqlite")

if _is_sqlite:
    # SQLite does not support connection pooling parameters.
    # StaticPool keeps a single in-process connection (fine for dev/test).
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        _url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DEBUG,
        future=True,
    )

    # Enable WAL mode and foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

else:
    # PostgreSQL (production)
    engine = create_engine(
        _url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        echo=settings.DEBUG,
        future=True,
    )


def check_db_connection() -> bool:
    """
    Returns True when a test SELECT reaches the database, False otherwise.
    Safe to call from a health-check endpoint.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except OperationalError:
        return False
