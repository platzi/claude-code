"""
Course rating endpoints.

Business errors are raised by CourseService as DomainError subclasses and
turned into {"detail", "code"} responses by the handler in app/main.py.
"""
from typing import List

from fastapi import APIRouter, Depends, Response, status

from app.core.deps import get_course_service
from app.core.security import get_current_user_id
from app.schemas.rating import (
    ErrorResponse,
    MyRatingRequest,
    RatingResponse,
    RatingStatsResponse,
)
from app.services.course_service import CourseService

router = APIRouter(prefix="/courses/{course_id}/ratings", tags=["ratings"])

COURSE_NOT_FOUND = {"model": ErrorResponse, "description": "Course not found (COURSE_NOT_FOUND)"}
UNAUTHENTICATED = {"model": ErrorResponse, "description": "Missing X-User-Id (UNAUTHENTICATED)"}


@router.get(
    "",
    response_model=List[RatingResponse],
    responses={404: COURSE_NOT_FOUND},
)
def get_course_ratings(
    course_id: int,
    course_service: CourseService = Depends(get_course_service),
) -> List[RatingResponse]:
    """Active ratings of a course, newest first (empty list if none)."""
    return [RatingResponse(**r) for r in course_service.get_course_ratings(course_id)]


@router.get(
    "/stats",
    response_model=RatingStatsResponse,
    responses={404: COURSE_NOT_FOUND},
)
def get_course_rating_stats(
    course_id: int,
    course_service: CourseService = Depends(get_course_service),
) -> RatingStatsResponse:
    """Average (0.0 if none), total and per-star distribution of active ratings."""
    return RatingStatsResponse(**course_service.get_course_rating_stats(course_id))


# ==================== CURRENT USER ("me") ====================

@router.get(
    "/me",
    response_model=RatingResponse,
    responses={
        401: UNAUTHENTICATED,
        404: {
            "model": ErrorResponse,
            "description": "RATING_NOT_FOUND if the user hasn't rated, COURSE_NOT_FOUND if the course doesn't exist",
        },
    },
)
def get_my_rating(
    course_id: int,
    user_id: int = Depends(get_current_user_id),
    course_service: CourseService = Depends(get_course_service),
) -> RatingResponse:
    """The current user's active rating for the course."""
    return RatingResponse(**course_service.get_user_course_rating(course_id, user_id))


@router.put(
    "/me",
    response_model=RatingResponse,
    responses={
        200: {"description": "Existing rating updated"},
        201: {"model": RatingResponse, "description": "Rating created"},
        401: UNAUTHENTICATED,
        404: COURSE_NOT_FOUND,
    },
)
def upsert_my_rating(
    course_id: int,
    rating_data: MyRatingRequest,
    response: Response,
    user_id: int = Depends(get_current_user_id),
    course_service: CourseService = Depends(get_course_service),
) -> RatingResponse:
    """
    Idempotent upsert of the current user's rating: 201 if it was created,
    200 if an existing active rating was updated.
    """
    rating, created = course_service.upsert_course_rating(
        course_id=course_id,
        user_id=user_id,
        rating=rating_data.rating,
    )
    if created:
        response.status_code = status.HTTP_201_CREATED
    return RatingResponse(**rating)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: UNAUTHENTICATED,
        404: {"model": ErrorResponse, "description": "User has no active rating (RATING_NOT_FOUND)"},
    },
)
def delete_my_rating(
    course_id: int,
    user_id: int = Depends(get_current_user_id),
    course_service: CourseService = Depends(get_course_service),
) -> None:
    """Soft delete of the current user's rating."""
    course_service.delete_course_rating(course_id, user_id)
