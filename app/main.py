from fastapi import FastAPI
from sqlalchemy import text

from app.db.session import engine, settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "MentorMatch API"}


@app.get("/health/db")
def database_health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "connected",
        }
    except Exception:
        return {
            "status": "error",
            "database": "unavailable",
        }
