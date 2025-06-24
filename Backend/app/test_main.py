import pytest
from unittest.mock import Mock
from fastapi.testclient import TestClient
from app.main import app, get_course_service
from app.services.course_service import CourseService


# Mock data according to the contracts
MOCK_COURSES_LIST = [
    {
        "id": 1,
        "name": "Curso de React",
        "description": "Aprende React desde cero",
        "thumbnail": "https://via.placeholder.com/150",
        "slug": "curso-de-react"
    },
    {
        "id": 2,
        "name": "Curso de Python",
        "description": "Domina Python paso a paso",
        "thumbnail": "https://via.placeholder.com/200",
        "slug": "curso-de-python"
    }
]

MOCK_COURSE_DETAIL = {
    "id": 1,
    "name": "Curso de React",
    "description": "Aprende React desde cero",
    "thumbnail": "https://via.placeholder.com/150",
    "slug": "curso-de-react",
    "teacher_id": [1, 2],
    "classes": [
        {
            "id": 1,
            "name": "Introducción a React",
            "description": "Conceptos básicos de React",
            "slug": "introduccion-a-react"
        },
        {
            "id": 2,
            "name": "Componentes en React",
            "description": "Aprende a crear componentes",
            "slug": "componentes-en-react"
        }
    ]
}


@pytest.fixture
def mock_course_service():
    """Create a mock CourseService for testing"""
    return Mock(spec=CourseService)


@pytest.fixture
def client(mock_course_service):
    """Create test client with mocked CourseService dependency"""
    
    def get_mock_course_service():
        return mock_course_service
    
    # Override the dependency
    app.dependency_overrides[get_course_service] = get_mock_course_service
    
    # Create test client
    client = TestClient(app)
    
    yield client
    
    # Clean up after test
    app.dependency_overrides.clear()


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_returns_welcome_message(self, client):
        """Test that root endpoint returns expected welcome message"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Bienvenido a Platziflix API"}


class TestHealthEndpoint:
    """Tests for the health check endpoint"""
    
    def test_health_endpoint_structure(self, client):
        """Test that health endpoint returns expected structure"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify required fields are present
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "database" in data
        
        # Verify field types
        assert isinstance(data["status"], str)
        assert isinstance(data["service"], str)
        assert isinstance(data["version"], str)
        assert isinstance(data["database"], bool)


class TestCoursesEndpoints:
    """Tests for courses related endpoints"""
    
    def test_get_all_courses_success(self, client, mock_course_service):
        """Test GET /courses returns list of courses matching contract"""
        # Configure mock
        mock_course_service.get_all_courses.return_value = MOCK_COURSES_LIST
        
        response = client.get("/courses")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify response is a list
        assert isinstance(data, list)
        assert len(data) == 2
        
        # Verify each course has required fields according to contract
        for course in data:
            assert "id" in course
            assert "name" in course
            assert "description" in course
            assert "thumbnail" in course
            assert "slug" in course
            
            # Verify field types
            assert isinstance(course["id"], int)
            assert isinstance(course["name"], str)
            assert isinstance(course["description"], str)
            assert isinstance(course["thumbnail"], str)
            assert isinstance(course["slug"], str)
        
        # Verify mock was called
        mock_course_service.get_all_courses.assert_called_once()
    
    def test_get_all_courses_empty_list(self, client, mock_course_service):
        """Test GET /courses when no courses exist"""
        # Configure mock to return empty list
        mock_course_service.get_all_courses.return_value = []
        
        response = client.get("/courses")
        assert response.status_code == 200
        assert response.json() == []
        
        mock_course_service.get_all_courses.assert_called_once()
    
    def test_get_course_by_slug_success(self, client, mock_course_service):
        """Test GET /courses/{slug} returns course details matching contract"""
        # Configure mock
        mock_course_service.get_course_by_slug.return_value = MOCK_COURSE_DETAIL
        
        response = client.get("/courses/curso-de-react")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify required fields according to contract
        assert "id" in data
        assert "name" in data
        assert "description" in data
        assert "thumbnail" in data
        assert "slug" in data
        assert "teacher_id" in data
        assert "classes" in data
        
        # Verify field types
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["description"], str)
        assert isinstance(data["thumbnail"], str)
        assert isinstance(data["slug"], str)
        assert isinstance(data["teacher_id"], list)
        assert isinstance(data["classes"], list)
        
        # Verify teacher_id contains integers
        for teacher_id in data["teacher_id"]:
            assert isinstance(teacher_id, int)
        
        # Verify classes structure
        for class_item in data["classes"]:
            assert "id" in class_item
            assert "name" in class_item
            assert "description" in class_item
            assert "slug" in class_item
            
            assert isinstance(class_item["id"], int)
            assert isinstance(class_item["name"], str)
            assert isinstance(class_item["description"], str)
            assert isinstance(class_item["slug"], str)
        
        # Verify mock was called with correct slug
        mock_course_service.get_course_by_slug.assert_called_once_with("curso-de-react")
    
    def test_get_course_by_slug_not_found(self, client, mock_course_service):
        """Test GET /courses/{slug} when course doesn't exist"""
        # Configure mock to return None
        mock_course_service.get_course_by_slug.return_value = None
        
        response = client.get("/courses/nonexistent-course")
        assert response.status_code == 404
        assert response.json() == {"detail": "Course not found"}
        
        mock_course_service.get_course_by_slug.assert_called_once_with("nonexistent-course")
    
    def test_get_course_by_slug_with_special_characters(self, client, mock_course_service):
        """Test GET /courses/{slug} with special characters in slug"""
        mock_course_service.get_course_by_slug.return_value = MOCK_COURSE_DETAIL
        
        response = client.get("/courses/curso-de-c++")
        assert response.status_code == 200
        
        mock_course_service.get_course_by_slug.assert_called_once_with("curso-de-c++")


class TestContractCompliance:
    """Additional tests to ensure strict contract compliance"""
    
    def test_courses_list_contract_fields_only(self, client, mock_course_service):
        """Ensure GET /courses response contains only contract-specified fields"""
        mock_course_service.get_all_courses.return_value = MOCK_COURSES_LIST
        
        response = client.get("/courses")
        data = response.json()
        
        expected_fields = {"id", "name", "description", "thumbnail", "slug"}
        
        for course in data:
            # Verify no extra fields beyond contract
            actual_fields = set(course.keys())
            assert actual_fields == expected_fields, f"Expected {expected_fields}, got {actual_fields}"
    
    def test_course_detail_contract_fields_only(self, client, mock_course_service):
        """Ensure GET /courses/{slug} response contains only contract-specified fields"""
        mock_course_service.get_course_by_slug.return_value = MOCK_COURSE_DETAIL
        
        response = client.get("/courses/curso-de-react")
        data = response.json()
        
        # Verify main course fields
        expected_course_fields = {"id", "name", "description", "thumbnail", "slug", "teacher_id", "classes"}
        actual_course_fields = set(data.keys())
        assert actual_course_fields == expected_course_fields
        
        # Verify classes fields
        expected_class_fields = {"id", "name", "description", "slug"}
        for class_item in data["classes"]:
            actual_class_fields = set(class_item.keys())
            assert actual_class_fields == expected_class_fields
    
    def test_courses_response_data_matches_contract_examples(self, client, mock_course_service):
        """Test that response structure exactly matches contract examples"""
        mock_course_service.get_all_courses.return_value = [
            {
                "id": 1,
                "name": "Curso de React",
                "description": "Curso de React",
                "thumbnail": "https://via.placeholder.com/150",
                "slug": "curso-de-react"
            }
        ]
        
        response = client.get("/courses")
        data = response.json()
        
        # Verify the response matches the exact contract structure
        assert len(data) == 1
        course = data[0]
        assert course["id"] == 1
        assert course["name"] == "Curso de React"
        assert course["description"] == "Curso de React"
        assert course["thumbnail"] == "https://via.placeholder.com/150"
        assert course["slug"] == "curso-de-react" 