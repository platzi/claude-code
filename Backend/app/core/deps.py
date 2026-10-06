"""
Shared FastAPI dependencies.

Lives outside app/main.py so routers can import it without a circular import.
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.services.course_service import CourseService


def get_course_service(db: Session = Depends(get_db)) -> CourseService:
    """
    Dependency to get CourseService instance
    """
    return CourseService(db)
