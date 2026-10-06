from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.core.config import settings
from app.core.deps import get_course_service
from app.db.base import engine
from app.routers import ratings
from app.services.course_service import CourseService
from app.services.exceptions import (
    CourseNotFoundError,
    DomainError,
    InvalidRatingError,
    NotAuthenticatedError,
    RatingNotFoundError,
)

app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="""
    Platziflix API - Platform for online courses

    ## Features

    * **Courses**: Browse and search courses
    * **Ratings**: Rate courses and view statistics
    * **Teachers**: Course instructors information
    * **Lessons**: Course content structure

    ## Rating System

    Users can rate courses from 1 (worst) to 5 (best).
    - One rating per user per course
    - Ratings can be updated or deleted
    - Aggregated statistics available per course
    - The current user is identified by the `X-User-Id` header (demo mode)

    Business errors respond with `{"detail": str, "code": str}`.
    """,
    openapi_tags=[
        {
            "name": "courses",
            "description": "Operations with courses"
        },
        {
            "name": "ratings",
            "description": "Course rating operations"
        },
        {
            "name": "health",
            "description": "Health check endpoints"
        }
    ]
)

# HTTP status for each domain error (unmapped DomainError subclasses -> 400).
DOMAIN_ERROR_STATUS: dict[type[DomainError], int] = {
    CourseNotFoundError: 404,
    RatingNotFoundError: 404,
    InvalidRatingError: 422,
    NotAuthenticatedError: 401,
}


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    status_code = next(
        (code for cls, code in DOMAIN_ERROR_STATUS.items() if isinstance(exc, cls)),
        400,
    )
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message, "code": exc.code},
    )


app.include_router(ratings.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Bienvenido a Platziflix API"}


@app.get("/health", tags=["health"])
def health() -> dict[str, str | bool | int]:
    """
    Health check endpoint that verifies:
    - Service status
    - Database connectivity
    """
    health_status = {
        "status": "ok",
        "service": settings.project_name,
        "version": settings.version,
        "database": False,
    }

    # Check database connectivity and verify migration
    try:
        with engine.connect() as connection:
            # Execute COUNT on courses table to verify migration was executed
            result = connection.execute(text("SELECT COUNT(*) FROM courses"))
            row = result.fetchone()
            if row:
                count = row[0]
                health_status["database"] = True
                health_status["courses_count"] = count
            else:
                health_status["database"] = True
                health_status["courses_count"] = 0
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["database_error"] = str(e)

    return health_status


@app.get("/courses", tags=["courses"])
def get_courses(course_service: CourseService = Depends(get_course_service)) -> list:
    """
    Get all courses.
    Returns a list of courses with basic information: id, name, description, thumbnail, slug
    """
    return course_service.get_all_courses()


@app.get("/courses/{slug}", tags=["courses"])
def get_course_by_slug(slug: str, course_service: CourseService = Depends(get_course_service)) -> dict:
    """
    Get course details by slug.
    Returns course information including teachers and classes.
    """
    course = course_service.get_course_by_slug(slug)

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return course


@app.get("/classes/{class_id}", tags=["courses"])
def get_class_by_id(class_id: int, course_service: CourseService = Depends(get_course_service)) -> dict:
    """
    Get lesson/class details by ID.
    Returns lesson information including video URL.
    """
    lesson = course_service.get_class_by_id(class_id)

    if not lesson:
        raise HTTPException(status_code=404, detail="Class not found")

    return lesson
