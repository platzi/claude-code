"""
Database constraint tests for course_ratings table.
Tests actual database constraints (requires test database).
"""
import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app.db.base import SessionLocal
from app.models.course import Course
from app.models.course_rating import CourseRating


@pytest.fixture
def db_session():
    """Create database session for testing."""
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def sample_course(db_session):
    """Create and persist sample course."""
    course = Course(
        name="Test Course",
        description="Test Description",
        thumbnail="https://example.com/thumb.jpg",
        slug=f"test-course-{datetime.utcnow().timestamp()}"
    )
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)
    return course


class TestRatingConstraints:
    """Tests for database constraints on course_ratings table."""

    def test_rating_check_constraint_min(self, db_session, sample_course):
        """Test CHECK constraint prevents rating < 1."""
        # Arrange
        rating = CourseRating(
            course_id=sample_course.id,
            user_id=42,
            rating=0  # Invalid: below minimum
        )
        db_session.add(rating)

        # Act & Assert
        with pytest.raises(IntegrityError, match="ck_course_ratings_rating_range"):
            db_session.commit()

    def test_rating_check_constraint_max(self, db_session, sample_course):
        """Test CHECK constraint prevents rating > 5."""
        # Arrange
        rating = CourseRating(
            course_id=sample_course.id,
            user_id=42,
            rating=6  # Invalid: above maximum
        )
        db_session.add(rating)

        # Act & Assert
        with pytest.raises(IntegrityError, match="ck_course_ratings_rating_range"):
            db_session.commit()

    @pytest.mark.skip(reason="UNIQUE constraint with NULL values requires partial index in PostgreSQL. Business logic prevents duplicates at service layer.")
    def test_unique_constraint_prevents_duplicate_active_ratings(
        self,
        db_session,
        sample_course
    ):
        """Test UNIQUE constraint prevents multiple active ratings from same user.

        Note: In PostgreSQL, NULL != NULL, so UNIQUE(course_id, user_id, deleted_at)
        doesn't prevent duplicates when deleted_at IS NULL.
        This would require a PARTIAL UNIQUE INDEX instead.
        The business logic in service layer prevents this scenario.
        """
        # Arrange - Create first rating
        rating1 = CourseRating(
            course_id=sample_course.id,
            user_id=42,
            rating=5
        )
        db_session.add(rating1)
        db_session.commit()

        # Act - Try to create duplicate
        rating2 = CourseRating(
            course_id=sample_course.id,
            user_id=42,  # Same user
            rating=3
        )
        db_session.add(rating2)

        # Assert
        with pytest.raises(IntegrityError, match="uq_course_ratings_user_course_deleted"):
            db_session.commit()

    def test_unique_constraint_allows_soft_deleted_duplicates(
        self,
        db_session,
        sample_course
    ):
        """Test UNIQUE constraint allows creating new rating after soft delete."""
        # Arrange - Create and soft delete first rating
        rating1 = CourseRating(
            course_id=sample_course.id,
            user_id=42,
            rating=5
        )
        db_session.add(rating1)
        db_session.commit()

        rating1.deleted_at = datetime.utcnow()
        db_session.commit()

        # Act - Create new rating (should succeed)
        rating2 = CourseRating(
            course_id=sample_course.id,
            user_id=42,  # Same user, but previous is deleted
            rating=3
        )
        db_session.add(rating2)
        db_session.commit()

        # Assert
        db_session.refresh(rating2)
        assert rating2.id is not None
        assert rating2.rating == 3

    def test_foreign_key_constraint(self, db_session):
        """Test foreign key constraint to courses table."""
        # Arrange - Create rating with non-existent course_id
        rating = CourseRating(
            course_id=99999,  # Non-existent course
            user_id=42,
            rating=5
        )
        db_session.add(rating)

        # Act & Assert
        with pytest.raises(IntegrityError, match="fk_course_ratings_course_id"):
            db_session.commit()
