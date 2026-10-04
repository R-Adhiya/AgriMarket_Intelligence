"""
Health check endpoints.

GET /api/health    — basic liveness check
GET /api/health/db — database connectivity check (safe, no credentials exposed)
"""

import logging

from fastapi import APIRouter
from pydantic import BaseModel

from app.database.connection import check_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    service: str


class DbHealthResponse(BaseModel):
    status: str
    database: str


@router.get("/health", response_model=HealthResponse, summary="Health Check")
def health_check():
    """
    Returns the health status of the API.
    Used by the frontend to verify backend connectivity.
    """
    return HealthResponse(
        status="healthy",
        service="AgriMarket Intelligence API",
    )


@router.get(
    "/health/db",
    response_model=DbHealthResponse,
    summary="Database Health Check",
)
def health_db():
    """
    Checks whether the database is reachable.
    Returns {"status": "healthy", "database": "connected"} on success.
    Returns {"status": "degraded", "database": "unreachable"} on failure.
    Never exposes connection strings or credentials.
    """
    reachable = check_db_connection()
    if reachable:
        logger.debug("Database health check: OK")
        return DbHealthResponse(status="healthy", database="connected")
    else:
        logger.warning("Database health check: FAILED")
        return DbHealthResponse(status="degraded", database="unreachable")
