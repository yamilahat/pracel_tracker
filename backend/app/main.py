from fastapi import FastAPI

from app.api.gmail import router as gmail_router
from app.api.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="Smart Parcel Tracker")
    app.include_router(health_router)
    app.include_router(gmail_router)
    return app


app = create_app()
