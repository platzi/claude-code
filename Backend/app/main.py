from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from app.core.config import settings
from app.db.base import engine

app = FastAPI(title=settings.project_name, version=settings.version)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Bienvenido a Platziflix API"}


@app.get("/health")
def health() -> dict[str, str | bool]:
    """
    Health check endpoint that verifies:
    - Service status
    - Database connectivity
    """
    health_status = {
        "status": "ok",
        "service": settings.project_name,
        "version": settings.version,
        "database": False
    }
    
    # Check database connectivity
    try:
        with engine.connect() as connection:
            # Execute SELECT 1 to test database connection
            result = connection.execute(text("SELECT 1"))
            if result.fetchone():
                health_status["database"] = True
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["database_error"] = str(e)
    
    return health_status
