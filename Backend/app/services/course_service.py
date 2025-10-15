from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.teacher import Teacher
from app.models.course_rating import CourseRating


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

        Returns:
            List of course dictionaries with: id, name, description, thumbnail, slug,
            average_rating, total_ratings
        """
        courses = self.db.query(Course).filter(Course.deleted_at.is_(None)).all()

        result = []
        for course in courses:
            # Obtener stats de ratings para cada curso
            try:
                rating_stats = self.get_course_rating_stats(course.id)
            except ValueError:
                # Si falla, usar valores por defecto
                rating_stats = {
                    "average_rating": 0.0,
                    "total_ratings": 0
                }

            result.append({
                "id": course.id,
                "name": course.name,
                "description": course.description,
                "thumbnail": course.thumbnail,
                "slug": course.slug,
                "average_rating": rating_stats["average_rating"],
                "total_ratings": rating_stats["total_ratings"]
            })

        return result

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

        # Obtener stats de ratings eficientemente
        try:
            rating_stats = self.get_course_rating_stats(course.id)
        except ValueError:
            # Si falla, usar valores por defecto
            rating_stats = {
                "average_rating": 0.0,
                "total_ratings": 0,
                "rating_distribution": {i: 0 for i in range(1, 6)}
            }

        return {
            "id": course.id,
            "name": course.name,
            "description": course.description,
            "thumbnail": course.thumbnail,
            "slug": course.slug,
            "teacher_id": [teacher.id for teacher in course.teachers],
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
            # NUEVOS CAMPOS DE RATING
            "average_rating": rating_stats["average_rating"],
            "total_ratings": rating_stats["total_ratings"],
            "rating_distribution": rating_stats["rating_distribution"]
        }

    def get_course_ratings(self, course_id: int) -> List[Dict[str, Any]]:
        """
        Get all active ratings for a specific course.

        Args:
            course_id: The course ID

        Returns:
            List of rating dictionaries with user_id, rating, timestamps

        Raises:
            ValueError: If course_id doesn't exist
        """
        # Validar que el curso exists
        course = self.db.query(Course).filter(
            Course.id == course_id,
            Course.deleted_at.is_(None)
        ).first()

        if not course:
            raise ValueError(f"Course with id {course_id} not found")

        # Query optimizado para obtener ratings
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

    def add_course_rating(
        self,
        course_id: int,
        user_id: int,
        rating: int
    ) -> Dict[str, Any]:
        """
        Add a new rating or update existing active rating for a course.

        Business Logic:
        - If user has active rating: UPDATE existing rating
        - If user has no active rating: CREATE new rating
        - Validates rating is between 1-5
        - Validates course exists

        Args:
            course_id: The course ID
            user_id: The user ID (no FK validation yet)
            rating: Rating value (1-5)

        Returns:
            Dictionary with created/updated rating data

        Raises:
            ValueError: If course doesn't exist or rating out of range
        """
        # Validar rating en rango
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        # Validar que el curso existe
        course = self.db.query(Course).filter(
            Course.id == course_id,
            Course.deleted_at.is_(None)
        ).first()

        if not course:
            raise ValueError(f"Course with id {course_id} not found")

        # Buscar rating existente ACTIVO del usuario para este curso
        existing_rating = (
            self.db.query(CourseRating)
            .filter(
                CourseRating.course_id == course_id,
                CourseRating.user_id == user_id,
                CourseRating.deleted_at.is_(None)
            )
            .first()
        )

        if existing_rating:
            # ACTUALIZAR rating existente
            existing_rating.rating = rating
            existing_rating.updated_at = datetime.utcnow()
            self.db.flush()
            self.db.commit()
            self.db.refresh(existing_rating)
            return existing_rating.to_dict()
        else:
            # CREAR nuevo rating
            new_rating = CourseRating(
                course_id=course_id,
                user_id=user_id,
                rating=rating
            )
            self.db.add(new_rating)
            self.db.commit()
            self.db.refresh(new_rating)
            return new_rating.to_dict()

    def update_course_rating(
        self,
        course_id: int,
        user_id: int,
        rating: int
    ) -> Dict[str, Any]:
        """
        Update an existing active rating.

        Note: This method is semantically identical to add_course_rating
        but provides explicit UPDATE semantics for REST API (PUT verb).

        Args:
            course_id: The course ID
            user_id: The user ID
            rating: New rating value (1-5)

        Returns:
            Dictionary with updated rating data

        Raises:
            ValueError: If rating doesn't exist or is inactive
        """
        # Validar rating en rango
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        # Buscar rating ACTIVO existente
        existing_rating = (
            self.db.query(CourseRating)
            .filter(
                CourseRating.course_id == course_id,
                CourseRating.user_id == user_id,
                CourseRating.deleted_at.is_(None)
            )
            .first()
        )

        if not existing_rating:
            raise ValueError(
                f"No active rating found for user {user_id} on course {course_id}"
            )

        # Actualizar rating
        existing_rating.rating = rating
        existing_rating.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(existing_rating)

        return existing_rating.to_dict()

    def delete_course_rating(self, course_id: int, user_id: int) -> bool:
        """
        Soft delete a course rating.

        Sets deleted_at timestamp instead of removing from database.
        This allows historical tracking and potential undeletion.

        Args:
            course_id: The course ID
            user_id: The user ID

        Returns:
            True if rating was deleted, False if rating not found
        """
        # Buscar rating ACTIVO
        rating_to_delete = (
            self.db.query(CourseRating)
            .filter(
                CourseRating.course_id == course_id,
                CourseRating.user_id == user_id,
                CourseRating.deleted_at.is_(None)
            )
            .first()
        )

        if not rating_to_delete:
            return False

        # Soft delete: establecer deleted_at
        rating_to_delete.deleted_at = datetime.utcnow()
        rating_to_delete.updated_at = datetime.utcnow()
        self.db.commit()

        return True

    def get_user_course_rating(
        self,
        course_id: int,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific user's rating for a course.

        Useful for:
        - Checking if user has already rated
        - Displaying user's current rating in UI
        - Preventing duplicate rating submissions

        Args:
            course_id: The course ID
            user_id: The user ID

        Returns:
            Rating dictionary if exists and active, None otherwise
        """
        # Buscar rating activo específico
        rating = (
            self.db.query(CourseRating)
            .filter(
                CourseRating.course_id == course_id,
                CourseRating.user_id == user_id,
                CourseRating.deleted_at.is_(None)
            )
            .first()
        )

        if not rating:
            return None

        return rating.to_dict()

    def get_course_rating_stats(self, course_id: int) -> Dict[str, Any]:
        """
        Get aggregated rating statistics for a course.

        Performs aggregation at database level for optimal performance.
        Use this instead of Course.average_rating property for API responses.

        Args:
            course_id: The course ID

        Returns:
            Dictionary with:
            - average_rating: float (0.0 if no ratings)
            - total_ratings: int
            - rating_distribution: dict with counts per rating value (1-5)
        """
        # Validar que el curso existe
        course = self.db.query(Course).filter(
            Course.id == course_id,
            Course.deleted_at.is_(None)
        ).first()

        if not course:
            raise ValueError(f"Course with id {course_id} not found")

        # Agregación SQL eficiente
        stats = (
            self.db.query(
                func.coalesce(func.avg(CourseRating.rating), 0.0).label('average'),
                func.count(CourseRating.id).label('total')
            )
            .filter(
                CourseRating.course_id == course_id,
                CourseRating.deleted_at.is_(None)
            )
            .first()
        )

        # Distribución de ratings (cuántos 1, 2, 3, 4, 5 estrellas)
        distribution_query = (
            self.db.query(
                CourseRating.rating,
                func.count(CourseRating.id).label('count')
            )
            .filter(
                CourseRating.course_id == course_id,
                CourseRating.deleted_at.is_(None)
            )
            .group_by(CourseRating.rating)
            .all()
        )

        # Construir diccionario de distribución
        rating_distribution = {i: 0 for i in range(1, 6)}
        for rating_value, count in distribution_query:
            rating_distribution[rating_value] = count

        return {
            "average_rating": round(float(stats.average), 2),
            "total_ratings": stats.total,
            "rating_distribution": rating_distribution
        } 