from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(title=settings.project_name, version=settings.version)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Bienvenido a Platziflix API"}


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.project_name,
        "version": settings.version,
    }
