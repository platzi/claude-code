"""
CourseService queries against the real database (transactional, see conftest.py).
"""
from datetime import datetime

import pytest
from sqlalchemy import event

from app.models.course import Course
from app.models.course_rating import CourseRating
from app.models.lesson import Lesson
from app.services.course_service import CourseService


def make_course(db_session, name: str) -> Course:
    course = Course(
        name=name,
        description="Test Description",
        thumbnail="https://example.com/thumb.jpg",
        slug=f"{name.lower().replace(' ', '-')}-{datetime.utcnow().timestamp()}",
    )
    db_session.add(course)
    db_session.flush()
    return course


def rate(db_session, course: Course, user_id: int, value: int, deleted: bool = False):
    db_session.add(CourseRating(
        course_id=course.id,
        user_id=user_id,
        rating=value,
        deleted_at=datetime.utcnow() if deleted else None,
    ))
    db_session.flush()


@pytest.fixture
def service(db_session):
    return CourseService(db_session)


def by_id(courses, course_id):
    return next(course for course in courses if course["id"] == course_id)


class TestGetAllCourses:

    def test_course_without_ratings_has_zero_stats(self, db_session, service):
        course = make_course(db_session, "Sin Ratings")

        result = by_id(service.get_all_courses(), course.id)

        assert result["average_rating"] == 0.0
        assert result["total_ratings"] == 0

    def test_stats_ignore_soft_deleted_ratings(self, db_session, service):
        course = make_course(db_session, "Con Ratings")
        rate(db_session, course, user_id=1, value=5)
        rate(db_session, course, user_id=2, value=2)
        rate(db_session, course, user_id=3, value=1, deleted=True)

        result = by_id(service.get_all_courses(), course.id)

        assert result["average_rating"] == 3.5
        assert result["total_ratings"] == 2

    def test_soft_deleted_courses_are_excluded(self, db_session, service):
        course = make_course(db_session, "Borrado")
        course.deleted_at = datetime.utcnow()
        db_session.flush()

        ids = [c["id"] for c in service.get_all_courses()]

        assert course.id not in ids

    def test_runs_a_constant_number_of_queries(self, db_session, service):
        for i in range(5):
            course = make_course(db_session, f"Curso N1 {i}")
            rate(db_session, course, user_id=1, value=4)

        statements = []

        def count(conn, cursor, statement, *args):
            statements.append(statement)

        engine = db_session.get_bind().engine
        event.listen(engine, "before_cursor_execute", count)
        try:
            service.get_all_courses()
        finally:
            event.remove(engine, "before_cursor_execute", count)

        assert len(statements) == 1


class TestRatingStats:

    def test_distribution_counts_active_ratings_per_star(self, db_session, service):
        course = make_course(db_session, "Distribucion")
        for user_id, value in [(1, 5), (2, 5), (3, 4), (4, 2)]:
            rate(db_session, course, user_id=user_id, value=value)
        rate(db_session, course, user_id=5, value=1, deleted=True)

        stats = service.get_course_rating_stats(course.id)

        assert stats == {
            "average_rating": 4.0,
            "total_ratings": 4,
            "rating_distribution": {1: 0, 2: 1, 3: 0, 4: 1, 5: 2},
        }


class TestGetClassById:

    def make_lesson(self, db_session, course, deleted=False):
        lesson = Lesson(
            course_id=course.id,
            name="Leccion",
            description="Desc",
            slug=f"leccion-{datetime.utcnow().timestamp()}",
            video_url="https://example.com/v.mp4",
            deleted_at=datetime.utcnow() if deleted else None,
        )
        db_session.add(lesson)
        db_session.flush()
        return lesson

    def test_returns_active_lesson(self, db_session, service):
        lesson = self.make_lesson(db_session, make_course(db_session, "Clases"))

        result = service.get_class_by_id(lesson.id)

        assert result["title"] == "Leccion"
        assert result["video"] == "https://example.com/v.mp4"

    def test_soft_deleted_lesson_is_not_found(self, db_session, service):
        lesson = self.make_lesson(db_session, make_course(db_session, "Clases"), deleted=True)

        assert service.get_class_by_id(lesson.id) is None

    def test_lesson_of_soft_deleted_course_is_not_found(self, db_session, service):
        course = make_course(db_session, "Clases")
        lesson = self.make_lesson(db_session, course)
        course.deleted_at = datetime.utcnow()
        db_session.flush()

        assert service.get_class_by_id(lesson.id) is None
