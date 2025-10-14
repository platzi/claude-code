"""
Pydantic schemas for course rating requests and responses.
Provides validation and serialization for API endpoints.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Dict


class RatingRequest(BaseModel):
    """
    Schema for creating or updating a course rating.

    Validation:
    - user_id must be positive integer
    - rating must be between 1 and 5 (inclusive)
    """
    user_id: int = Field(
        ...,
        gt=0,
        description="ID of the user submitting the rating"
    )
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="Rating value from 1 (worst) to 5 (best)"
    )

    @field_validator('rating')
    @classmethod
    def validate_rating_range(cls, v: int) -> int:
        """Additional validation for rating range."""
        if not 1 <= v <= 5:
            raise ValueError('Rating must be between 1 and 5')
        return v


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

    class Config:
        from_attributes = True


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

    class Config:
        json_schema_extra = {
            "example": {
                "average_rating": 4.35,
                "total_ratings": 142,
                "rating_distribution": {
                    1: 5,
                    2: 10,
                    3: 25,
                    4: 50,
                    5: 52
                }
            }
        }


class ErrorResponse(BaseModel):
    """
    Standard error response schema.
    Used for validation errors and business logic errors.
    """
    detail: str
    error_code: str | None = None
