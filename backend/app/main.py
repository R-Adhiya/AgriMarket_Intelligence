from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.farmer import router as farmer_router
from app.api.market import router as market_router
from app.api.transport import router as transport_router
from app.api.prediction import router as prediction_router

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
app.include_router(market_router)
app.include_router(transport_router)
app.include_router(prediction_router)


@app.get("/", include_in_schema=False)
def root():
    return {
        "message": "AgriMarket Intelligence API",
        "docs": "/docs",
        "health": "/api/health",
    }
