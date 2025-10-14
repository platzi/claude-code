from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from .base import BaseModel


class Course(BaseModel):
    """
    Course model representing online courses in the platform.
    """
    __tablename__ = 'courses'
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    thumbnail = Column(String(500), nullable=False)  # URL to thumbnail image
    slug = Column(String(255), nullable=False, unique=True, index=True)
    
    # Many-to-many relationship with Teacher
    teachers = relationship(
        "Teacher", 
        secondary="course_teachers", 
        back_populates="courses"
    )
    
    # One-to-many relationship with Lesson
    lessons = relationship(
        "Lesson",
        back_populates="course",
        cascade="all, delete-orphan"
    )

    # One-to-many relationship with CourseRating
    ratings = relationship(
        "CourseRating",
        back_populates="course",
        cascade="all, delete-orphan",
        lazy='select'  # Lazy loading por defecto, eager cuando se necesite
    )

    @property
    def average_rating(self) -> float:
        """
        Calculate average rating from active (non-deleted) ratings.

        Returns:
            float: Average rating (0.0 if no ratings exist)

        Note: This is a Python-level calculation. For better performance
        on large datasets, use the service layer method that calculates
        at the database level.
        """
        # Filtrar solo ratings activos (deleted_at IS NULL)
        active_ratings = [r.rating for r in self.ratings if r.deleted_at is None]

        if not active_ratings:
            return 0.0

        return round(sum(active_ratings) / len(active_ratings), 2)

    @property
    def total_ratings(self) -> int:
        """
        Count total active (non-deleted) ratings.

        Returns:
            int: Number of active ratings
        """
        return len([r for r in self.ratings if r.deleted_at is None])

    def __repr__(self):
        return f"<Course(id={self.id}, name='{self.name}', slug='{self.slug}')>" 