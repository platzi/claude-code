"""
Domain exceptions raised by the service layer.

Each exception carries a stable machine-readable `code`. The HTTP mapping
(status codes) lives in app/main.py, so services stay transport-agnostic.
"""


class DomainError(Exception):
    """Base class for business errors that are reported to API clients."""

    code = "DOMAIN_ERROR"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class CourseNotFoundError(DomainError):
    code = "COURSE_NOT_FOUND"

    def __init__(self, course_id: int):
        super().__init__(f"Course with id {course_id} not found")


class RatingNotFoundError(DomainError):
    code = "RATING_NOT_FOUND"

    def __init__(self, message: str = "User has not rated this course"):
        super().__init__(message)


class InvalidRatingError(DomainError):
    code = "INVALID_RATING"

    def __init__(self, rating: int):
        super().__init__(f"Rating must be between 1 and 5, got {rating}")


class NotAuthenticatedError(DomainError):
    code = "UNAUTHENTICATED"

    def __init__(self, message: str = "Not authenticated"):
        super().__init__(message)
