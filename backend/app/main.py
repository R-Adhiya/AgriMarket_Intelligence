from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AgriMarket Intelligence — helping farmers make smarter selling decisions.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
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


@app.on_event("startup")
def on_startup():
    """Auto-create tables and seed dev data when using SQLite (local dev)."""
    if settings.DATABASE_URL.startswith("sqlite"):
        from app.database.connection import engine
        from app.database.base import Base
        # Import all models so their tables are registered with Base.metadata
        import app.models  # noqa: F401
        Base.metadata.create_all(bind=engine)

        # Seed development data (idempotent)
        try:
            from app.database.seed import seed
            seed()
        except Exception as e:
            print(f"[startup] seed skipped: {e}")


@app.get("/", include_in_schema=False)
def root():
    return {
        "message": "AgriMarket Intelligence API",
        "docs": "/docs",
        "health": "/api/health",
    }
