"""
SQLAlchemy session factory and FastAPI dependency.
"""

from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from app.database.connection import engine

SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency — yields a database session per request
    and ensures it is closed when the request finishes.

    Usage in a route:
        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
