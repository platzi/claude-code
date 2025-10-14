"""
Integration tests for course rating API endpoints.
Tests HTTP interface with mocked service layer.
"""
import pytest
from unittest.mock import Mock
from fastapi.testclient import TestClient
from app.main import app, get_course_service
from app.services.course_service import CourseService


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


class TestAddCourseRatingEndpoint:
    """Tests for POST /courses/{course_id}/ratings"""

    def test_add_rating_success(self, client, mock_course_service):
        """Test successfully adding a new rating."""
        # Arrange
        mock_course_service.add_course_rating.return_value = MOCK_RATING

        # Act
        response = client.post(
            "/courses/1/ratings",
            json={"user_id": 42, "rating": 5}
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == 5
        assert data["user_id"] == 42
        mock_course_service.add_course_rating.assert_called_once_with(
            course_id=1,
            user_id=42,
            rating=5
        )

    def test_add_rating_invalid_rating_value(self, client, mock_course_service):
        """Test adding rating with invalid value (Pydantic validation)."""
        # Act
        response = client.post(
            "/courses/1/ratings",
            json={"user_id": 42, "rating": 6}
        )

        # Assert
        assert response.status_code == 422  # Unprocessable Entity (Pydantic validation)

    def test_add_rating_course_not_found(self, client, mock_course_service):
        """Test adding rating to non-existent course."""
        # Arrange
        mock_course_service.add_course_rating.side_effect = ValueError("Course with id 999 not found")

        # Act
        response = client.post(
            "/courses/999/ratings",
            json={"user_id": 42, "rating": 5}
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_add_rating_missing_fields(self, client, mock_course_service):
        """Test adding rating with missing required fields."""
        # Act
        response = client.post(
            "/courses/1/ratings",
            json={"user_id": 42}  # Missing rating
        )

        # Assert
        assert response.status_code == 422


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
        mock_course_service.get_course_ratings.side_effect = ValueError("Course with id 999 not found")

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
        mock_course_service.get_course_rating_stats.side_effect = ValueError("Course with id 999 not found")

        # Act
        response = client.get("/courses/999/ratings/stats")

        # Assert
        assert response.status_code == 404


class TestGetUserCourseRatingEndpoint:
    """Tests for GET /courses/{course_id}/ratings/user/{user_id}"""

    def test_get_user_rating_exists(self, client, mock_course_service):
        """Test retrieving existing user rating."""
        # Arrange
        mock_course_service.get_user_course_rating.return_value = MOCK_RATING

        # Act
        response = client.get("/courses/1/ratings/user/42")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == 42
        assert data["rating"] == 5

    def test_get_user_rating_not_exists(self, client, mock_course_service):
        """Test retrieving non-existent user rating."""
        # Arrange
        mock_course_service.get_user_course_rating.return_value = None

        # Act
        response = client.get("/courses/1/ratings/user/42")

        # Assert
        assert response.status_code == 204


class TestUpdateCourseRatingEndpoint:
    """Tests for PUT /courses/{course_id}/ratings/{user_id}"""

    def test_update_rating_success(self, client, mock_course_service):
        """Test successfully updating a rating."""
        # Arrange
        updated_rating = MOCK_RATING.copy()
        updated_rating["rating"] = 3
        mock_course_service.update_course_rating.return_value = updated_rating

        # Act
        response = client.put(
            "/courses/1/ratings/42",
            json={"user_id": 42, "rating": 3}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == 3

    def test_update_rating_user_id_mismatch(self, client, mock_course_service):
        """Test updating with mismatched user_id in path and body."""
        # Act
        response = client.put(
            "/courses/1/ratings/42",
            json={"user_id": 99, "rating": 3}  # Different user_id
        )

        # Assert
        assert response.status_code == 400
        assert "must match" in response.json()["detail"]

    def test_update_rating_not_found(self, client, mock_course_service):
        """Test updating non-existent rating."""
        # Arrange
        mock_course_service.update_course_rating.side_effect = ValueError("No active rating found")

        # Act
        response = client.put(
            "/courses/1/ratings/42",
            json={"user_id": 42, "rating": 3}
        )

        # Assert
        assert response.status_code == 404


class TestDeleteCourseRatingEndpoint:
    """Tests for DELETE /courses/{course_id}/ratings/{user_id}"""

    def test_delete_rating_success(self, client, mock_course_service):
        """Test successfully deleting a rating."""
        # Arrange
        mock_course_service.delete_course_rating.return_value = True

        # Act
        response = client.delete("/courses/1/ratings/42")

        # Assert
        assert response.status_code == 204
        mock_course_service.delete_course_rating.assert_called_once_with(1, 42)

    def test_delete_rating_not_found(self, client, mock_course_service):
        """Test deleting non-existent rating."""
        # Arrange
        mock_course_service.delete_course_rating.return_value = False

        # Act
        response = client.delete("/courses/1/ratings/42")

        # Assert
        assert response.status_code == 404


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
