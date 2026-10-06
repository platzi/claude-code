"""
Integration tests for course rating API endpoints.
Tests HTTP interface with mocked service layer.
"""
import pytest
from unittest.mock import Mock
from fastapi.testclient import TestClient
from app.main import app
from app.core.deps import get_course_service
from app.core.security import get_current_user_id
from app.services.course_service import CourseService
from app.services.exceptions import (
    CourseNotFoundError,
    InvalidRatingError,
    RatingNotFoundError,
)


MOCK_RATING = {
    "id": 1,
    "course_id": 1,
    "user_id": 42,
    "rating": 5,
    "created_at": "2025-10-14T10:30:00",
    "updated_at": "2025-10-14T10:30:00"
}

MOCK_RATING_STATS = {
    "average_rating": 4.35,
    "total_ratings": 142,
    "rating_distribution": {1: 5, 2: 10, 3: 25, 4: 50, 5: 52}
}


@pytest.fixture
def mock_course_service():
    """Create mock CourseService for testing."""
    return Mock(spec=CourseService)


@pytest.fixture
def client(mock_course_service):
    """Create test client with mocked dependencies."""
    def get_mock_course_service():
        return mock_course_service

    app.dependency_overrides[get_course_service] = get_mock_course_service
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestGetCourseRatingsEndpoint:
    """Tests for GET /courses/{course_id}/ratings"""

    def test_get_ratings_success(self, client, mock_course_service):
        """Test retrieving course ratings."""
        # Arrange
        mock_course_service.get_course_ratings.return_value = [MOCK_RATING]

        # Act
        response = client.get("/courses/1/ratings")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["rating"] == 5

    def test_get_ratings_empty(self, client, mock_course_service):
        """Test retrieving ratings for course with no ratings."""
        # Arrange
        mock_course_service.get_course_ratings.return_value = []

        # Act
        response = client.get("/courses/1/ratings")

        # Assert
        assert response.status_code == 200
        assert response.json() == []

    def test_get_ratings_course_not_found(self, client, mock_course_service):
        """Test retrieving ratings for non-existent course."""
        # Arrange
        mock_course_service.get_course_ratings.side_effect = CourseNotFoundError(999)

        # Act
        response = client.get("/courses/999/ratings")

        # Assert
        assert response.status_code == 404


class TestGetCourseRatingStatsEndpoint:
    """Tests for GET /courses/{course_id}/ratings/stats"""

    def test_get_stats_success(self, client, mock_course_service):
        """Test retrieving rating statistics."""
        # Arrange
        mock_course_service.get_course_rating_stats.return_value = MOCK_RATING_STATS

        # Act
        response = client.get("/courses/1/ratings/stats")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["average_rating"] == 4.35
        assert data["total_ratings"] == 142
        assert "rating_distribution" in data

    def test_get_stats_course_not_found(self, client, mock_course_service):
        """Test retrieving stats for non-existent course."""
        # Arrange
        mock_course_service.get_course_rating_stats.side_effect = CourseNotFoundError(999)

        # Act
        response = client.get("/courses/999/ratings/stats")

        # Assert
        assert response.status_code == 404
        assert response.json()["code"] == "COURSE_NOT_FOUND"


@pytest.fixture
def authed_client(client):
    """Client whose current user is 42 (overrides the X-User-Id dependency)."""
    app.dependency_overrides[get_current_user_id] = lambda: 42
    return client


class TestMyRatingEndpoints:
    """Tests for /courses/{course_id}/ratings/me"""

    @pytest.mark.parametrize("method", ["get", "put", "delete"])
    def test_missing_user_header_returns_401(self, client, mock_course_service, method):
        kwargs = {"json": {"rating": 4}} if method == "put" else {}

        response = getattr(client, method)("/courses/1/ratings/me", **kwargs)

        assert response.status_code == 401
        assert response.json() == {"detail": "Not authenticated", "code": "UNAUTHENTICATED"}
        assert not mock_course_service.method_calls

    def test_user_id_comes_from_x_user_id_header(self, client, mock_course_service):
        mock_course_service.get_user_course_rating.return_value = MOCK_RATING

        response = client.get("/courses/1/ratings/me", headers={"X-User-Id": "42"})

        assert response.status_code == 200
        mock_course_service.get_user_course_rating.assert_called_once_with(1, 42)

    def test_non_positive_user_header_is_rejected(self, client, mock_course_service):
        response = client.get("/courses/1/ratings/me", headers={"X-User-Id": "0"})

        assert response.status_code == 422
        mock_course_service.get_user_course_rating.assert_not_called()

    def test_get_my_rating_success(self, authed_client, mock_course_service):
        mock_course_service.get_user_course_rating.return_value = MOCK_RATING

        response = authed_client.get("/courses/1/ratings/me")

        assert response.status_code == 200
        assert response.json() == MOCK_RATING

    def test_get_my_rating_not_rated_returns_404_with_code(self, authed_client, mock_course_service):
        mock_course_service.get_user_course_rating.side_effect = RatingNotFoundError()

        response = authed_client.get("/courses/1/ratings/me")

        assert response.status_code == 404
        assert response.json() == {
            "detail": "User has not rated this course",
            "code": "RATING_NOT_FOUND",
        }

    def test_get_my_rating_course_not_found(self, authed_client, mock_course_service):
        mock_course_service.get_user_course_rating.side_effect = CourseNotFoundError(999)

        response = authed_client.get("/courses/999/ratings/me")

        assert response.status_code == 404
        assert response.json()["code"] == "COURSE_NOT_FOUND"

    def test_put_creates_rating_returns_201(self, authed_client, mock_course_service):
        mock_course_service.upsert_course_rating.return_value = (MOCK_RATING, True)

        response = authed_client.put("/courses/1/ratings/me", json={"rating": 5})

        assert response.status_code == 201
        assert response.json() == MOCK_RATING
        mock_course_service.upsert_course_rating.assert_called_once_with(
            course_id=1, user_id=42, rating=5
        )

    def test_put_updates_rating_returns_200(self, authed_client, mock_course_service):
        mock_course_service.upsert_course_rating.return_value = ({**MOCK_RATING, "rating": 3}, False)

        response = authed_client.put("/courses/1/ratings/me", json={"rating": 3})

        assert response.status_code == 200
        assert response.json()["rating"] == 3

    def test_put_ignores_user_id_in_body(self, authed_client, mock_course_service):
        mock_course_service.upsert_course_rating.return_value = (MOCK_RATING, True)

        authed_client.put("/courses/1/ratings/me", json={"rating": 5, "user_id": 999})

        assert mock_course_service.upsert_course_rating.call_args.kwargs["user_id"] == 42

    @pytest.mark.parametrize("rating", [0, 6, "cinco"])
    def test_put_invalid_rating_returns_422(self, authed_client, mock_course_service, rating):
        response = authed_client.put("/courses/1/ratings/me", json={"rating": rating})

        assert response.status_code == 422
        mock_course_service.upsert_course_rating.assert_not_called()

    def test_put_invalid_rating_from_service_returns_422_with_code(self, authed_client, mock_course_service):
        mock_course_service.upsert_course_rating.side_effect = InvalidRatingError(9)

        response = authed_client.put("/courses/1/ratings/me", json={"rating": 5})

        assert response.status_code == 422
        assert response.json()["code"] == "INVALID_RATING"

    def test_put_course_not_found(self, authed_client, mock_course_service):
        mock_course_service.upsert_course_rating.side_effect = CourseNotFoundError(999)

        response = authed_client.put("/courses/999/ratings/me", json={"rating": 5})

        assert response.status_code == 404
        assert response.json()["code"] == "COURSE_NOT_FOUND"

    def test_delete_my_rating_returns_204(self, authed_client, mock_course_service):
        response = authed_client.delete("/courses/1/ratings/me")

        assert response.status_code == 204
        assert response.content == b""
        mock_course_service.delete_course_rating.assert_called_once_with(1, 42)

    def test_delete_my_rating_not_found(self, authed_client, mock_course_service):
        mock_course_service.delete_course_rating.side_effect = RatingNotFoundError()

        response = authed_client.delete("/courses/1/ratings/me")

        assert response.status_code == 404
        assert response.json()["code"] == "RATING_NOT_FOUND"


class TestRatingEndpointsContractCompliance:
    """Tests to ensure API contract compliance."""

    def test_rating_response_structure(self, client, mock_course_service):
        """Verify rating response contains exactly expected fields."""
        # Arrange
        mock_course_service.get_course_ratings.return_value = [MOCK_RATING]

        # Act
        response = client.get("/courses/1/ratings")
        data = response.json()

        # Assert
        expected_fields = {"id", "course_id", "user_id", "rating", "created_at", "updated_at"}
        actual_fields = set(data[0].keys())
        assert actual_fields == expected_fields

    def test_stats_response_structure(self, client, mock_course_service):
        """Verify stats response contains exactly expected fields."""
        # Arrange
        mock_course_service.get_course_rating_stats.return_value = MOCK_RATING_STATS

        # Act
        response = client.get("/courses/1/ratings/stats")
        data = response.json()

        # Assert
        expected_fields = {"average_rating", "total_ratings", "rating_distribution"}
        actual_fields = set(data.keys())
        assert actual_fields == expected_fields
