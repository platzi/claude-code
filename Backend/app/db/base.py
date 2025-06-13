from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator

from app.core.config import settings
from app.models.base import Base

# Create SQLAlchemy engine
engine = create_engine(settings.database_url)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency function for getting database session
def get_db() -> Generator:
    """
    Dependency function that yields database session.
    Used for dependency injection in FastAPI endpoints.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
