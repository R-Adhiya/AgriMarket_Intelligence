"""
AgriMarket Intelligence — FastAPI application entry point.

Phase 12 additions:
  - Structured logging configuration
  - Global exception handler (safe 500 responses, no stack-trace leakage)
  - Security headers middleware
  - Validated CORS origins from settings
"""

import logging
import logging.config

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.farmer import router as farmer_router
from app.api.buyer import router as buyer_router
from app.api.interests import router as interests_router
from app.api.market import router as market_router
from app.api.transport import router as transport_router
from app.api.prediction import router as prediction_router
from app.api.recommendation import router as recommendation_router
from app.api.dashboard import router as dashboard_router
from app.api.admin import router as admin_router

# ── Logging ───────────────────────────────────────────────────────────────────

_LOG_LEVEL = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        }
    },
    "root": {"level": _LOG_LEVEL, "handlers": ["console"]},
    # Quieten noisy third-party loggers
    "loggers": {
        "uvicorn.access": {"level": "WARNING"},
        "passlib": {"level": "WARNING"},
    },
})

logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AgriMarket Intelligence — helping farmers make smarter selling decisions.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Security headers middleware ────────────────────────────────────────────────


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject basic security headers on every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response


app.add_middleware(SecurityHeadersMiddleware)

# ── CORS ──────────────────────────────────────────────────────────────────────

# Build the allowed origins list from settings; always include FRONTEND_URL.
_cors_origins = list(settings.CORS_ORIGINS)
if settings.FRONTEND_URL and settings.FRONTEND_URL not in _cors_origins:
    _cors_origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global exception handler ──────────────────────────────────────────────────


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Catch-all for unexpected exceptions.
    Logs the full traceback internally; returns a safe opaque message to the client.
    """
    logger.exception(
        "Unhandled exception on %s %s", request.method, request.url.path
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred. Please try again later.",
            "code": "INTERNAL_ERROR",
        },
    )


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(farmer_router)
app.include_router(buyer_router)
app.include_router(interests_router)
app.include_router(market_router)
app.include_router(transport_router)
app.include_router(prediction_router)
app.include_router(recommendation_router)
app.include_router(dashboard_router)
app.include_router(admin_router)


# ── Lifecycle events ──────────────────────────────────────────────────────────


@app.on_event("startup")
def on_startup():
    logger.info("AgriMarket Intelligence API starting up (version %s)", settings.APP_VERSION)
    if settings.DATABASE_URL.startswith("sqlite"):
        from app.database.connection import engine
        from app.database.base import Base
        import app.models  # noqa: F401
        Base.metadata.create_all(bind=engine)
        try:
            from app.database.seed import seed
            seed()
        except Exception as e:
            logger.warning("Seed skipped: %s", e)
    logger.info("Startup complete — docs at /docs")


@app.on_event("shutdown")
def on_shutdown():
    logger.info("AgriMarket Intelligence API shutting down")


# ── Root ──────────────────────────────────────────────────────────────────────


@app.get("/", include_in_schema=False)
def root():
    return {
        "message": "AgriMarket Intelligence API",
        "docs": "/docs",
        "health": "/api/health",
    }
