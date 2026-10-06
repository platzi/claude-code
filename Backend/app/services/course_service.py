from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from sqlalchemy.exc import IntegrityError
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.course_rating import CourseRating
from app.services.exceptions import (
    CourseNotFoundError,
    InvalidRatingError,
    RatingNotFoundError,
)

RATING_VALUES = range(1, 6)


class CourseService:
    """
    Service class for handling course-related operations.
    Implements the contract specifications for course endpoints.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_all_courses(self) -> List[Dict[str, Any]]:
        """
        Get all courses with basic information including rating stats.

        A single query: courses LEFT JOIN active ratings, grouped by course,
        so the cost doesn't grow with the number of courses (no N+1).

        Returns:
            List of course dictionaries with: id, name, description, thumbnail, slug,
            average_rating, total_ratings
        """
        rows = (
            self.db.query(
                Course,
                func.coalesce(func.avg(CourseRating.rating), 0).label("average"),
                func.count(CourseRating.id).label("total"),
            )
            .outerjoin(
                CourseRating,
                and_(
                    CourseRating.course_id == Course.id,
                    CourseRating.deleted_at.is_(None),
                ),
            )
            .filter(Course.deleted_at.is_(None))
            .group_by(Course.id)
            .order_by(Course.id)
            .all()
        )

        return [
            {
                "id": course.id,
                "name": course.name,
                "description": course.description,
                "thumbnail": course.thumbnail,
                "slug": course.slug,
                "average_rating": round(float(average), 2),
                "total_ratings": total,
            }
            for course, average, total in rows
        ]

    def get_course_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Get course details by slug including teachers and lessons.
        
        Args:
            slug: The course slug
            
        Returns:
            Course dictionary with teachers and lessons, or None if not found
        """
        course = (
            self.db.query(Course)
            .options(
                joinedload(Course.teachers),
                joinedload(Course.lessons)
            )
            .filter(Course.slug == slug)
            .filter(Course.deleted_at.is_(None))
            .first()
        )
        
        if not course:
            return None

        rating_stats = self._compute_rating_stats(course.id)

        return {
            "id": course.id,
            "name": course.name,
            "description": course.description,
            "thumbnail": course.thumbnail,
            "slug": course.slug,
            "teacher_id": [teacher.id for teacher in course.teachers],
            "teachers": [
                {"id": teacher.id, "name": teacher.name}
                for teacher in course.teachers
            ],
            "classes": [
                {
                    "id": lesson.id,
                    "name": lesson.name,
                    "description": lesson.description,
                    "slug": lesson.slug
                }
                for lesson in course.lessons
                if lesson.deleted_at is None
            ],
            "average_rating": rating_stats["average_rating"],
            "total_ratings": rating_stats["total_ratings"],
            "rating_distribution": rating_stats["rating_distribution"]
        }

    def get_class_by_id(self, class_id: int) -> Optional[Dict[str, Any]]:
        """
        Get lesson ("class" in the API) details by ID.

        Soft-deleted lessons, and lessons of soft-deleted courses, are not found.

        Returns:
            Lesson dictionary with video URL, or None if not found
        """
        lesson = (
            self.db.query(Lesson)
            .join(Course, Lesson.course_id == Course.id)
            .filter(
                Lesson.id == class_id,
                Lesson.deleted_at.is_(None),
                Course.deleted_at.is_(None),
            )
            .first()
        )

        if not lesson:
            return None

        return {
            "id": lesson.id,
            "title": lesson.name,
            "description": lesson.description,
            "slug": lesson.slug,
            "video": lesson.video_url,
            "duration": 0  # TODO: agregar duración si está disponible
        }

    def _ensure_course_exists(self, course_id: int) -> None:
        """Raise CourseNotFoundError unless an active course with that id exists."""
        course = self.db.query(Course).filter(
            Course.id == course_id,
            Course.deleted_at.is_(None)
        ).first()

        if not course:
            raise CourseNotFoundError(course_id)

    def _get_active_rating(self, course_id: int, user_id: int) -> Optional[CourseRating]:
        return (
            self.db.query(CourseRating)
            .filter(
                CourseRating.course_id == course_id,
                CourseRating.user_id == user_id,
                CourseRating.deleted_at.is_(None)
            )
            .first()
        )

    def get_course_ratings(self, course_id: int) -> List[Dict[str, Any]]:
        """
        Get all active ratings for a specific course.

        Args:
            course_id: The course ID

        Returns:
            List of rating dictionaries with user_id, rating, timestamps

        Raises:
            CourseNotFoundError: If course_id doesn't exist
        """
        self._ensure_course_exists(course_id)

        ratings = (
            self.db.query(CourseRating)
            .filter(
                CourseRating.course_id == course_id,
                CourseRating.deleted_at.is_(None)
            )
            .order_by(CourseRating.created_at.desc())
            .all()
        )

        return [rating.to_dict() for rating in ratings]

    def upsert_course_rating(
        self,
        course_id: int,
        user_id: int,
        rating: int
    ) -> Tuple[Dict[str, Any], bool]:
        """
        Create the user's active rating for a course, or update it if it exists.

        Concurrency: the partial unique index uq_course_ratings_active_user_course
        rejects a second active rating. If a concurrent request wins the race
        between our SELECT and INSERT, we roll back and update its row instead.

        Args:
            course_id: The course ID
            user_id: The user ID (no FK validation yet)
            rating: Rating value (1-5)

        Returns:
            (rating dictionary, created) where created is True only if a new
            row was inserted.

        Raises:
            InvalidRatingError: If rating is out of range
            CourseNotFoundError: If course doesn't exist
        """
        if not 1 <= rating <= 5:
            raise InvalidRatingError(rating)

        self._ensure_course_exists(course_id)

        existing_rating = self._get_active_rating(course_id, user_id)
        if existing_rating:
            return self._apply_rating(existing_rating, rating), False

        new_rating = CourseRating(
            course_id=course_id,
            user_id=user_id,
            rating=rating
        )
        self.db.add(new_rating)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            existing_rating = self._get_active_rating(course_id, user_id)
            if existing_rating is None:
                raise
            return self._apply_rating(existing_rating, rating), False

        self.db.refresh(new_rating)
        return new_rating.to_dict(), True

    def _apply_rating(self, course_rating: CourseRating, rating: int) -> Dict[str, Any]:
        course_rating.rating = rating
        course_rating.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(course_rating)
        return course_rating.to_dict()

    def delete_course_rating(self, course_id: int, user_id: int) -> None:
        """
        Soft delete the user's active rating (sets deleted_at).

        Raises:
            RatingNotFoundError: If the user has no active rating
        """
        rating_to_delete = self._get_active_rating(course_id, user_id)
        if not rating_to_delete:
            raise RatingNotFoundError()

        now = datetime.utcnow()
        rating_to_delete.deleted_at = now
        rating_to_delete.updated_at = now
        self.db.commit()

    def get_user_course_rating(
        self,
        course_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Get a specific user's active rating for a course.

        Raises:
            CourseNotFoundError: If course doesn't exist
            RatingNotFoundError: If the user hasn't rated the course
        """
        self._ensure_course_exists(course_id)

        rating = self._get_active_rating(course_id, user_id)
        if not rating:
            raise RatingNotFoundError()

        return rating.to_dict()

    def get_course_rating_stats(self, course_id: int) -> Dict[str, Any]:
        """
        Get aggregated rating statistics for a course.

        Args:
            course_id: The course ID

        Returns:
            Dictionary with:
            - average_rating: float (0.0 if no ratings)
            - total_ratings: int
            - rating_distribution: dict with counts per rating value (1-5)

        Raises:
            CourseNotFoundError: If course doesn't exist
        """
        self._ensure_course_exists(course_id)
        return self._compute_rating_stats(course_id)

    def _compute_rating_stats(self, course_id: int) -> Dict[str, Any]:
        """Average, total and per-star distribution in a single aggregate query."""
        stats = (
            self.db.query(
                func.coalesce(func.avg(CourseRating.rating), 0).label("average"),
                func.count(CourseRating.id).label("total"),
                *(
                    func.count(CourseRating.id)
                    .filter(CourseRating.rating == value)
                    .label(f"stars_{value}")
                    for value in RATING_VALUES
                ),
            )
            .filter(
                CourseRating.course_id == course_id,
                CourseRating.deleted_at.is_(None)
            )
            .one()
        )

        return {
            "average_rating": round(float(stats.average), 2),
            "total_ratings": stats.total,
            "rating_distribution": {
                value: getattr(stats, f"stars_{value}") for value in RATING_VALUES
            },
        }
