from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes import applications, auth, departments, interests, projects, recommendations
from app.db.session import engine, settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(departments.router)
api_router.include_router(projects.router)
api_router.include_router(interests.router)
api_router.include_router(recommendations.router)
api_router.include_router(applications.router)
app.include_router(api_router)


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
