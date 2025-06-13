"""
Seed data script for Platziflix database.
This script creates sample data for testing and development.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.models import Teacher, Course, Lesson, course_teachers
from app.core.config import settings


def create_sample_data():
    """Create sample data for testing."""
    db: Session = SessionLocal()

    try:
        # Create sample teachers
        teacher1 = Teacher(
            name="Juan Pérez",
            email="juan.perez@platziflix.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        teacher2 = Teacher(
            name="María García",
            email="maria.garcia@platziflix.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        teacher3 = Teacher(
            name="Carlos Rodríguez",
            email="carlos.rodriguez@platziflix.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.add_all([teacher1, teacher2, teacher3])
        db.commit()

        # Create sample courses
        course1 = Course(
            name="Curso de React",
            description="Aprende React desde cero hasta convertirte en un desarrollador profesional",
            thumbnail="https://via.placeholder.com/300x200?text=React+Course",
            slug="curso-de-react",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        course2 = Course(
            name="Curso de Python",
            description="Domina Python y sus frameworks más populares",
            thumbnail="https://via.placeholder.com/300x200?text=Python+Course",
            slug="curso-de-python",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        course3 = Course(
            name="Curso de JavaScript",
            description="JavaScript moderno y sus mejores prácticas",
            thumbnail="https://via.placeholder.com/300x200?text=JavaScript+Course",
            slug="curso-de-javascript",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.add_all([course1, course2, course3])
        db.commit()

        # Assign teachers to courses (many-to-many)
        course1.teachers.append(teacher1)
        course1.teachers.append(teacher2)
        course2.teachers.append(teacher2)
        course2.teachers.append(teacher3)
        course3.teachers.append(teacher1)
        course3.teachers.append(teacher3)

        db.commit()

        # Create sample lessons
        lessons_data = [
            # React course lessons
            {
                "course": course1,
                "name": "Introducción a React",
                "description": "Conceptos básicos de React y JSX",
                "slug": "introduccion-a-react",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            },
            {
                "course": course1,
                "name": "Componentes y Props",
                "description": "Creación de componentes reutilizables",
                "slug": "componentes-y-props",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            },
            {
                "course": course1,
                "name": "Estado y Eventos",
                "description": "Manejo del estado y eventos en React",
                "slug": "estado-y-eventos",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            },
            # Python course lessons
            {
                "course": course2,
                "name": "Introducción a Python",
                "description": "Sintaxis básica y tipos de datos",
                "slug": "introduccion-a-python",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            },
            {
                "course": course2,
                "name": "Funciones y Módulos",
                "description": "Organización del código con funciones",
                "slug": "funciones-y-modulos",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            },
            # JavaScript course lessons
            {
                "course": course3,
                "name": "JavaScript Moderno",
                "description": "ES6+ y nuevas características",
                "slug": "javascript-moderno",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            },
        ]

        for lesson_data in lessons_data:
            lesson = Lesson(
                course_id=lesson_data["course"].id,
                name=lesson_data["name"],
                description=lesson_data["description"],
                slug=lesson_data["slug"],
                video_url=lesson_data["video_url"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(lesson)

        db.commit()

        print("✅ Sample data created successfully!")
        print(f"   - Created {len([teacher1, teacher2, teacher3])} teachers")
        print(f"   - Created {len([course1, course2, course3])} courses")
        print(f"   - Created {len(lessons_data)} lessons")

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating sample data: {e}")
        raise
    finally:
        db.close()


def clear_all_data():
    """Clear all data from the database."""
    db: Session = SessionLocal()

    try:
        # Delete in reverse order to avoid foreign key constraints
        db.query(Lesson).delete()
        db.execute(course_teachers.delete())
        db.query(Course).delete()
        db.query(Teacher).delete()
        db.commit()

        print("✅ All data cleared successfully!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error clearing data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        clear_all_data()
    else:
        create_sample_data()
