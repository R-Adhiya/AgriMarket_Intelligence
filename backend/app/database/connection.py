"""
SQLAlchemy engine and connection-pool configuration.
Reads DATABASE_URL from the environment via app.core.config.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.core.config import settings

# Connection pool tuned for a typical web-service workload.
# pool_pre_ping probes a connection before returning it from the pool,
# so stale/dropped connections are replaced automatically.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=settings.DEBUG,          # SQL logging only when DEBUG=true
    future=True,                  # SQLAlchemy 2.x style
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
