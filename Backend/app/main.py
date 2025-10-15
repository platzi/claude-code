from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List
from app.core.config import settings
from app.db.base import engine, get_db
from app.services.course_service import CourseService
from app.schemas.rating import (
    RatingRequest,
    RatingResponse,
    RatingStatsResponse,
    ErrorResponse
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


def get_course_service(db: Session = Depends(get_db)) -> CourseService:
    """
    Dependency to get CourseService instance
    """
    return CourseService(db)


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
def get_class_by_id(class_id: int, db: Session = Depends(get_db)) -> dict:
    """
    Get lesson/class details by ID.
    Returns lesson information including video URL.
    """
    from app.models import Lesson

    lesson = db.query(Lesson).filter(Lesson.id == class_id).first()

    if not lesson:
        raise HTTPException(status_code=404, detail="Class not found")

    return {
        "id": lesson.id,
        "title": lesson.name,
        "description": lesson.description,
        "slug": lesson.slug,
        "video": lesson.video_url,
        "duration": 0  # TODO: agregar duración si está disponible
    }


# ==================== RATING ENDPOINTS ====================

@app.post(
    "/courses/{course_id}/ratings",
    response_model=RatingResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["ratings"],
    responses={
        201: {"description": "Rating created successfully"},
        400: {"model": ErrorResponse, "description": "Validation error"},
        404: {"model": ErrorResponse, "description": "Course not found"}
    }
)
def add_course_rating(
    course_id: int,
    rating_data: RatingRequest,
    course_service: CourseService = Depends(get_course_service)
) -> RatingResponse:
    """
    Add a new rating to a course or update existing rating.

    Business Logic:
    - If user already has an active rating: UPDATE existing
    - If user has no active rating: CREATE new rating
    - Returns HTTP 201 for new ratings

    Request Body:
    - user_id: User ID (positive integer)
    - rating: Rating value (1-5)

    Example:
        POST /courses/1/ratings
        {
            "user_id": 42,
            "rating": 5
        }
    """
    try:
        result = course_service.add_course_rating(
            course_id=course_id,
            user_id=rating_data.user_id,
            rating=rating_data.rating
        )
        return RatingResponse(**result)
    except ValueError as e:
        # Course not found or rating out of range
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )


@app.get(
    "/courses/{course_id}/ratings",
    response_model=List[RatingResponse],
    tags=["ratings"],
    responses={
        200: {"description": "List of course ratings"},
        404: {"model": ErrorResponse, "description": "Course not found"}
    }
)
def get_course_ratings(
    course_id: int,
    course_service: CourseService = Depends(get_course_service)
) -> List[RatingResponse]:
    """
    Get all active ratings for a course.

    Returns list of ratings ordered by creation date (newest first).
    Returns empty list if course has no ratings.

    Example:
        GET /courses/1/ratings

        Response:
        [
            {
                "id": 1,
                "course_id": 1,
                "user_id": 42,
                "rating": 5,
                "created_at": "2025-10-14T10:30:00",
                "updated_at": "2025-10-14T10:30:00"
            },
            ...
        ]
    """
    try:
        ratings = course_service.get_course_ratings(course_id)
        return [RatingResponse(**rating) for rating in ratings]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@app.get(
    "/courses/{course_id}/ratings/stats",
    response_model=RatingStatsResponse,
    tags=["ratings"],
    responses={
        200: {"description": "Course rating statistics"},
        404: {"model": ErrorResponse, "description": "Course not found"}
    }
)
def get_course_rating_stats(
    course_id: int,
    course_service: CourseService = Depends(get_course_service)
) -> RatingStatsResponse:
    """
    Get aggregated rating statistics for a course.

    Returns:
    - average_rating: Average of all active ratings (0.0 if none)
    - total_ratings: Count of active ratings
    - rating_distribution: Count per rating value (1-5)

    Example:
        GET /courses/1/ratings/stats

        Response:
        {
            "average_rating": 4.35,
            "total_ratings": 142,
            "rating_distribution": {
                "1": 5,
                "2": 10,
                "3": 25,
                "4": 50,
                "5": 52
            }
        }
    """
    try:
        stats = course_service.get_course_rating_stats(course_id)
        return RatingStatsResponse(**stats)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@app.get(
    "/courses/{course_id}/ratings/user/{user_id}",
    response_model=RatingResponse | None,
    tags=["ratings"],
    responses={
        200: {"description": "User's rating for the course"},
        204: {"description": "User has not rated this course"}
    }
)
def get_user_course_rating(
    course_id: int,
    user_id: int,
    course_service: CourseService = Depends(get_course_service)
) -> RatingResponse | None:
    """
    Get a specific user's rating for a course.

    Returns:
    - Rating object if user has rated the course
    - 204 No Content if user hasn't rated

    Use Case:
    - Check if current user has already rated before showing rating UI
    - Display user's current rating in course detail page

    Example:
        GET /courses/1/ratings/user/42

        Response (if rated):
        {
            "id": 123,
            "course_id": 1,
            "user_id": 42,
            "rating": 4,
            "created_at": "2025-10-14T10:30:00",
            "updated_at": "2025-10-14T10:30:00"
        }

        Response (if not rated):
        HTTP 204 No Content
    """
    rating = course_service.get_user_course_rating(course_id, user_id)

    if rating is None:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT
        )

    return RatingResponse(**rating)


@app.put(
    "/courses/{course_id}/ratings/{user_id}",
    response_model=RatingResponse,
    tags=["ratings"],
    responses={
        200: {"description": "Rating updated successfully"},
        400: {"model": ErrorResponse, "description": "Validation error"},
        404: {"model": ErrorResponse, "description": "Rating not found"}
    }
)
def update_course_rating(
    course_id: int,
    user_id: int,
    rating_data: RatingRequest,
    course_service: CourseService = Depends(get_course_service)
) -> RatingResponse:
    """
    Update an existing course rating.

    Semantics: PUT = Update existing resource
    Fails with 404 if rating doesn't exist (use POST to create).

    Request Body:
    - user_id: Must match path parameter (validation)
    - rating: New rating value (1-5)

    Example:
        PUT /courses/1/ratings/42
        {
            "user_id": 42,
            "rating": 3
        }
    """
    # Validar que user_id del body coincide con user_id del path
    if rating_data.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id in body must match user_id in path"
        )

    try:
        result = course_service.update_course_rating(
            course_id=course_id,
            user_id=user_id,
            rating=rating_data.rating
        )
        return RatingResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@app.delete(
    "/courses/{course_id}/ratings/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["ratings"],
    responses={
        204: {"description": "Rating deleted successfully"},
        404: {"model": ErrorResponse, "description": "Rating not found"}
    }
)
def delete_course_rating(
    course_id: int,
    user_id: int,
    course_service: CourseService = Depends(get_course_service)
) -> None:
    """
    Delete (soft delete) a course rating.

    Sets deleted_at timestamp, preserving data for historical analysis.
    Returns HTTP 204 No Content on success.
    Returns HTTP 404 if rating doesn't exist or already deleted.

    Example:
        DELETE /courses/1/ratings/42

        Response:
        HTTP 204 No Content
    """
    success = course_service.delete_course_rating(course_id, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active rating found for user {user_id} on course {course_id}"
        )

    return None
