from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import SessionLocal

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
    }


@app.get("/health/db")
def database_health_check() -> dict[str, str]:
    with SessionLocal() as session:
        session.execute(text("SELECT 1"))

    return {"status": "ok", "database": "connected"}
