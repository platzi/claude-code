from sqlalchemy import Column, Integer, ForeignKey, CheckConstraint, Index, text
from sqlalchemy.orm import relationship
from .base import BaseModel


class CourseRating(BaseModel):
    """
    CourseRating model representing user ratings for courses.

    Business Rules:
    - Rating must be between 1 and 5 (validated at DB and application level)
    - One active rating per user per course, enforced by the partial unique
      index uq_course_ratings_active_user_course (course_id, user_id)
      WHERE deleted_at IS NULL. Soft-deleted rows are excluded, so a user can
      delete and re-rate as many times as needed.
    - Supports soft deletes via deleted_at field

    Relationships:
    - Many ratings belong to one Course. The course_id FK has no ON DELETE
      rule on purpose: courses are never physically deleted (soft delete).
    """
    __tablename__ = 'course_ratings'
    __table_args__ = (
        Index(
            'uq_course_ratings_active_user_course',
            'course_id',
            'user_id',
            unique=True,
            postgresql_where=text('deleted_at IS NULL'),
        ),
    )

    # Foreign keys
    course_id = Column(
        Integer,
        ForeignKey('courses.id', name='fk_course_ratings_course_id'),
        nullable=False,
        index=True  # Ya creado en migración, documentado aquí
    )
    user_id = Column(
        Integer,
        nullable=False,
        index=True  # Ya creado en migración, documentado aquí
    )

    # Rating value
    rating = Column(
        Integer,
        CheckConstraint('rating >= 1 AND rating <= 5', name='ck_course_ratings_rating_range'),
        nullable=False
    )

    # Relationships
    course = relationship(
        "Course",
        back_populates="ratings"
    )

    def __repr__(self):
        return (
            f"<CourseRating("
            f"id={self.id}, "
            f"course_id={self.course_id}, "
            f"user_id={self.user_id}, "
            f"rating={self.rating}"
            f")>"
        )

    def to_dict(self):
        """
        Convert model to dictionary for API responses.
        Excludes deleted_at for cleaner API responses.
        """
        return {
            "id": self.id,
            "course_id": self.course_id,
            "user_id": self.user_id,
            "rating": self.rating,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
