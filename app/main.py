from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database import init_db
from app.routers import (
    auth_router,
    users_router,
    parts_router,
    stations_router,
    trace_router,
    metrics_router,
    ai_router
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Eventos del ciclo de vida: inicio y cierre"""
    # Inicio
    await init_db()
    print(f"{settings.app_name} v{settings.app_version} started")
    yield
    # Cierre
    print("👋 Application shutdown")


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API Backend para Trazabilidad de Producción Industrial",
    lifespan=lifespan
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Endpoint raíz
@app.get("/")
async def root():
    return {
        "message": "Ibero-Axon Production Tracking API",
        "version": settings.app_version,
        "status": "online"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Incluir routers
app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(parts_router.router)
app.include_router(stations_router.router)
app.include_router(trace_router.router)
app.include_router(metrics_router.router)
app.include_router(ai_router.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
