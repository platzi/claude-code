"""
Unit tests for CourseService rating methods.
Tests business logic in isolation using mocked database.
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app.services.course_service import CourseService
from app.models.course import Course
from app.models.course_rating import CourseRating
from app.services.exceptions import (
    CourseNotFoundError,
    InvalidRatingError,
    RatingNotFoundError,
)


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    return Mock()


@pytest.fixture
def course_service(mock_db_session):
    """Create CourseService with mocked database."""
    return CourseService(db=mock_db_session)


@pytest.fixture
def sample_course():
    """Create sample course for testing."""
    course = Course(
        id=1,
        name="Test Course",
        description="Test Description",
        thumbnail="https://example.com/thumb.jpg",
        slug="test-course",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        deleted_at=None
    )
    return course


@pytest.fixture
def sample_rating():
    """Create sample rating for testing."""
    rating = CourseRating(
        id=1,
        course_id=1,
        user_id=42,
        rating=5,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        deleted_at=None
    )
    return rating


class TestGetCourseRatings:
    """Tests for get_course_ratings method."""

    def test_get_ratings_success(
        self,
        course_service,
        mock_db_session,
        sample_course,
        sample_rating
    ):
        """Test retrieving ratings for existing course."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_course
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [sample_rating]

        # Act
        result = course_service.get_course_ratings(course_id=1)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["rating"] == 5
        assert result[0]["user_id"] == 42

    def test_get_ratings_course_not_found(self, course_service, mock_db_session):
        """Test retrieving ratings for non-existent course."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(CourseNotFoundError, match="Course with id 1 not found"):
            course_service.get_course_ratings(course_id=1)

    def test_get_ratings_empty_list(
        self,
        course_service,
        mock_db_session,
        sample_course
    ):
        """Test retrieving ratings for course with no ratings."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_course
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        # Act
        result = course_service.get_course_ratings(course_id=1)

        # Assert
        assert result == []


class TestUpsertCourseRating:
    """Tests for upsert_course_rating method."""

    def test_creates_rating_when_user_has_none(
        self,
        course_service,
        mock_db_session,
        sample_course
    ):
        """Creates a new rating and reports created=True."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            sample_course,  # Course exists check
            None  # No existing rating
        ]
        mock_db_session.refresh = Mock(side_effect=lambda obj: setattr(obj, 'id', 1))

        # Act
        result, created = course_service.upsert_course_rating(
            course_id=1,
            user_id=42,
            rating=5
        )

        # Assert
        assert created is True
        assert result["rating"] == 5
        assert result["user_id"] == 42
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_updates_existing_rating(
        self,
        course_service,
        mock_db_session,
        sample_course,
        sample_rating
    ):
        """Updates the active rating instead of creating a duplicate (created=False)."""
        # Arrange
        sample_rating.rating = 3  # Original rating
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            sample_course,  # Course exists
            sample_rating  # Existing rating
        ]

        # Act
        result, created = course_service.upsert_course_rating(
            course_id=1,
            user_id=42,
            rating=5  # New rating
        )

        # Assert
        assert created is False
        assert sample_rating.rating == 5
        assert result["rating"] == 5
        mock_db_session.commit.assert_called_once()
        mock_db_session.add.assert_not_called()

    def test_race_condition_updates_existing(
        self,
        course_service,
        mock_db_session,
        sample_course,
        sample_rating
    ):
        """Concurrent insert hitting the unique index falls back to UPDATE."""
        # Arrange
        sample_rating.rating = 3
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            sample_course,  # Course exists
            None,  # No active rating at SELECT time
            sample_rating  # Rating created by the concurrent request
        ]
        mock_db_session.commit.side_effect = [
            IntegrityError("INSERT", {}, Exception("uq_course_ratings_active_user_course")),
            None
        ]

        # Act
        result, created = course_service.upsert_course_rating(course_id=1, user_id=42, rating=5)

        # Assert
        mock_db_session.rollback.assert_called_once()
        assert created is False
        assert sample_rating.rating == 5
        assert result["rating"] == 5
        assert mock_db_session.commit.call_count == 2

    def test_integrity_error_without_existing_is_reraised(
        self,
        course_service,
        mock_db_session,
        sample_course
    ):
        """IntegrityError is re-raised when no active rating is found after rollback."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            sample_course,
            None,
            None
        ]
        mock_db_session.commit.side_effect = IntegrityError("INSERT", {}, Exception("boom"))

        # Act & Assert
        with pytest.raises(IntegrityError):
            course_service.upsert_course_rating(course_id=1, user_id=42, rating=5)
        mock_db_session.rollback.assert_called_once()

    @pytest.mark.parametrize("rating", [0, 6])
    def test_invalid_range(self, course_service, mock_db_session, rating):
        """Out-of-range ratings raise InvalidRatingError before touching the DB."""
        with pytest.raises(InvalidRatingError):
            course_service.upsert_course_rating(course_id=1, user_id=42, rating=rating)
        mock_db_session.query.assert_not_called()

    def test_course_not_found(self, course_service, mock_db_session):
        """Rating a non-existent course raises CourseNotFoundError."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(CourseNotFoundError, match="Course with id 999 not found"):
            course_service.upsert_course_rating(course_id=999, user_id=42, rating=5)


class TestDeleteCourseRating:
    """Tests for delete_course_rating method."""

    def test_delete_rating_success(
        self,
        course_service,
        mock_db_session,
        sample_rating
    ):
        """Test soft deleting existing rating."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_rating

        # Act
        course_service.delete_course_rating(course_id=1, user_id=42)

        # Assert
        assert sample_rating.deleted_at is not None
        mock_db_session.commit.assert_called_once()

    def test_delete_nonexistent_rating(self, course_service, mock_db_session):
        """Test deleting rating that doesn't exist."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(RatingNotFoundError):
            course_service.delete_course_rating(course_id=1, user_id=42)
        mock_db_session.commit.assert_not_called()


class TestGetUserCourseRating:
    """Tests for get_user_course_rating method."""

    def test_get_user_rating_exists(
        self,
        course_service,
        mock_db_session,
        sample_course,
        sample_rating
    ):
        """Test retrieving existing user rating."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            sample_course,
            sample_rating
        ]

        # Act
        result = course_service.get_user_course_rating(course_id=1, user_id=42)

        # Assert
        assert result is not None
        assert result["rating"] == 5
        assert result["user_id"] == 42

    def test_get_user_rating_not_exists(self, course_service, mock_db_session, sample_course):
        """User without an active rating raises RatingNotFoundError."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            sample_course,
            None
        ]

        # Act & Assert
        with pytest.raises(RatingNotFoundError):
            course_service.get_user_course_rating(course_id=1, user_id=42)

    def test_get_user_rating_course_not_found(self, course_service, mock_db_session):
        """Non-existent course raises CourseNotFoundError, not RatingNotFoundError."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(CourseNotFoundError):
            course_service.get_user_course_rating(course_id=999, user_id=42)


class TestGetCourseRatingStats:
    """Tests for get_course_rating_stats method."""

    @staticmethod
    def stats_row(average, total, distribution):
        return Mock(
            average=average,
            total=total,
            **{f"stars_{value}": distribution.get(value, 0) for value in range(1, 6)}
        )

    def test_get_stats_with_ratings(
        self,
        course_service,
        mock_db_session,
        sample_course
    ):
        """Average, total and distribution come from one aggregate row."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_course
        mock_db_session.query.return_value.filter.return_value.one.return_value = self.stats_row(
            4.5, 10, {5: 6, 4: 3, 3: 1}
        )

        # Act
        result = course_service.get_course_rating_stats(course_id=1)

        # Assert
        assert result == {
            "average_rating": 4.5,
            "total_ratings": 10,
            "rating_distribution": {1: 0, 2: 0, 3: 1, 4: 3, 5: 6},
        }

    def test_get_stats_no_ratings(
        self,
        course_service,
        mock_db_session,
        sample_course
    ):
        """Course without ratings returns zeros."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_course
        mock_db_session.query.return_value.filter.return_value.one.return_value = self.stats_row(
            0, 0, {}
        )

        # Act
        result = course_service.get_course_rating_stats(course_id=1)

        # Assert
        assert result["average_rating"] == 0.0
        assert result["total_ratings"] == 0
        assert all(count == 0 for count in result["rating_distribution"].values())

    def test_get_stats_course_not_found(self, course_service, mock_db_session):
        """Test retrieving stats for non-existent course."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(CourseNotFoundError, match="Course with id 999 not found"):
            course_service.get_course_rating_stats(course_id=999)
