from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.health import router as health_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AgriMarket Intelligence — helping farmers make smarter selling decisions.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow the Vite dev server (configurable via .env)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health_router)


@app.get("/", include_in_schema=False)
def root():
    return {
        "message": "AgriMarket Intelligence API",
        "docs": "/docs",
        "health": "/api/health",
    }
