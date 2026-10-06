"""
Pydantic schemas for course rating requests and responses.
Provides validation and serialization for API endpoints.
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Dict


class MyRatingRequest(BaseModel):
    """
    Body of PUT /courses/{course_id}/ratings/me.
    The user comes from get_current_user_id(), never from the body.
    """
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="Rating value from 1 (worst) to 5 (best)"
    )


class RatingResponse(BaseModel):
    """
    Schema for rating response in API.
    Matches the structure returned by CourseRating.to_dict()
    """
    id: int
    course_id: int
    user_id: int
    rating: int
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class RatingStatsResponse(BaseModel):
    """
    Schema for aggregated rating statistics.
    Used in course detail responses.
    """
    average_rating: float = Field(
        ...,
        ge=0.0,
        le=5.0,
        description="Average rating (0.0 if no ratings)"
    )
    total_ratings: int = Field(
        ...,
        ge=0,
        description="Total number of active ratings"
    )
    rating_distribution: Dict[int, int] = Field(
        ...,
        description="Count of ratings per value (1-5)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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
        }
    )


class ErrorResponse(BaseModel):
    """
    Standard error response schema.
    Used for validation errors and business logic errors.
    """
    detail: str
    code: str
