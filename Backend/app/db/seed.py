"""
Seed data script for Platziflix database.
This script creates sample data for testing and development.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.models import Teacher, Course, Lesson, course_teachers, CourseRating
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

        teacher4 = Teacher(
            name="Ana Martínez",
            email="ana.martinez@platziflix.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        teacher5 = Teacher(
            name="Diego López",
            email="diego.lopez@platziflix.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        teacher6 = Teacher(
            name="Sofía Torres",
            email="sofia.torres@platziflix.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.add_all([teacher1, teacher2, teacher3, teacher4, teacher5, teacher6])
        db.commit()

        # Create sample courses
        course1 = Course(
            name="Curso de React",
            description="Aprende React desde cero hasta convertirte en un desarrollador profesional",
            thumbnail="https://placehold.co/300x200/61dafb/1a1a2e?text=React",
            slug="curso-de-react",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        course2 = Course(
            name="Curso de Python",
            description="Domina Python y sus frameworks más populares",
            thumbnail="https://placehold.co/300x200/3572A5/ffffff?text=Python",
            slug="curso-de-python",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        course3 = Course(
            name="Curso de JavaScript",
            description="JavaScript moderno y sus mejores prácticas",
            thumbnail="https://placehold.co/300x200/f7df1e/1a1a2e?text=JavaScript",
            slug="curso-de-javascript",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        course4 = Course(
            name="Curso de TypeScript",
            description="Tipado estático para proyectos JavaScript escalables y robustos",
            thumbnail="https://placehold.co/300x200/3178c6/ffffff?text=TypeScript",
            slug="curso-de-typescript",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        course5 = Course(
            name="Curso de Vue.js",
            description="Construye interfaces reactivas con el framework progresivo de JavaScript",
            thumbnail="https://placehold.co/300x200/42b883/ffffff?text=Vue.js",
            slug="curso-de-vuejs",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        course6 = Course(
            name="Curso de Node.js",
            description="Desarrollo backend con JavaScript, APIs REST y manejo de bases de datos",
            thumbnail="https://placehold.co/300x200/68a063/ffffff?text=Node.js",
            slug="curso-de-nodejs",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        course7 = Course(
            name="Curso de Docker",
            description="Contenedores, imágenes y orquestación con Docker y Docker Compose",
            thumbnail="https://placehold.co/300x200/2496ed/ffffff?text=Docker",
            slug="curso-de-docker",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        course8 = Course(
            name="Curso de CSS Avanzado",
            description="Flexbox, Grid, animaciones y diseño responsive profesional",
            thumbnail="https://placehold.co/300x200/264de4/ffffff?text=CSS",
            slug="curso-de-css-avanzado",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        course9 = Course(
            name="Curso de Angular",
            description="Framework empresarial de Google para aplicaciones web de gran escala",
            thumbnail="https://placehold.co/300x200/dd0031/ffffff?text=Angular",
            slug="curso-de-angular",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.add_all([course1, course2, course3, course4, course5, course6, course7, course8, course9])
        db.commit()

        # Assign teachers to courses (many-to-many)
        course1.teachers.append(teacher1)
        course1.teachers.append(teacher2)
        course2.teachers.append(teacher2)
        course2.teachers.append(teacher3)
        course3.teachers.append(teacher1)
        course3.teachers.append(teacher3)
        course4.teachers.append(teacher4)
        course4.teachers.append(teacher1)
        course5.teachers.append(teacher5)
        course5.teachers.append(teacher2)
        course6.teachers.append(teacher3)
        course6.teachers.append(teacher6)
        course7.teachers.append(teacher4)
        course7.teachers.append(teacher5)
        course8.teachers.append(teacher6)
        course8.teachers.append(teacher2)
        course9.teachers.append(teacher5)
        course9.teachers.append(teacher3)

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
            # TypeScript course lessons
            {
                "course": course4,
                "name": "Tipos y Interfaces",
                "description": "Sistema de tipos de TypeScript desde cero",
                "slug": "tipos-e-interfaces",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            },
            {
                "course": course4,
                "name": "Generics y Decoradores",
                "description": "Patrones avanzados de TypeScript",
                "slug": "generics-y-decoradores",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            },
            {
                "course": course4,
                "name": "TypeScript con React",
                "description": "Integración de TypeScript en proyectos React",
                "slug": "typescript-con-react",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            },
            # Vue.js course lessons
            {
                "course": course5,
                "name": "Fundamentos de Vue.js",
                "description": "Directivas, componentes y reactividad",
                "slug": "fundamentos-de-vuejs",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            },
            {
                "course": course5,
                "name": "Vue Router y Vuex",
                "description": "Navegación y manejo de estado global",
                "slug": "vue-router-y-vuex",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            },
            # Node.js course lessons
            {
                "course": course6,
                "name": "Servidor HTTP con Node",
                "description": "Creación de servidores y manejo de peticiones",
                "slug": "servidor-http-con-node",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            },
            {
                "course": course6,
                "name": "Express y Middlewares",
                "description": "Framework Express y arquitectura de middlewares",
                "slug": "express-y-middlewares",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            },
            {
                "course": course6,
                "name": "APIs REST con Node",
                "description": "Diseño y construcción de APIs RESTful",
                "slug": "apis-rest-con-node",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            },
            # Docker course lessons
            {
                "course": course7,
                "name": "Imágenes y Contenedores",
                "description": "Conceptos fundamentales de Docker",
                "slug": "imagenes-y-contenedores",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            },
            {
                "course": course7,
                "name": "Docker Compose",
                "description": "Orquestación de múltiples contenedores",
                "slug": "docker-compose",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            },
            # CSS course lessons
            {
                "course": course8,
                "name": "Flexbox Completo",
                "description": "Diseño unidimensional con Flexbox",
                "slug": "flexbox-completo",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            },
            {
                "course": course8,
                "name": "CSS Grid Layout",
                "description": "Diseño bidimensional con CSS Grid",
                "slug": "css-grid-layout",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            },
            {
                "course": course8,
                "name": "Animaciones CSS",
                "description": "Transiciones, keyframes y animaciones complejas",
                "slug": "animaciones-css",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            },
            # Angular course lessons
            {
                "course": course9,
                "name": "Componentes Angular",
                "description": "Arquitectura basada en componentes con Angular",
                "slug": "componentes-angular",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            },
            {
                "course": course9,
                "name": "Servicios e Inyección de Dependencias",
                "description": "Sistema de DI de Angular y servicios HTTP",
                "slug": "servicios-e-inyeccion-dependencias",
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

        # Create sample ratings
        ratings_data = [
            # React course: ~4.2 average
            {"course": course1, "user_id": 1, "rating": 5},
            {"course": course1, "user_id": 2, "rating": 4},
            {"course": course1, "user_id": 3, "rating": 5},
            {"course": course1, "user_id": 4, "rating": 4},
            {"course": course1, "user_id": 5, "rating": 3},
            # Python course: ~4.6 average
            {"course": course2, "user_id": 1, "rating": 5},
            {"course": course2, "user_id": 2, "rating": 5},
            {"course": course2, "user_id": 3, "rating": 4},
            {"course": course2, "user_id": 4, "rating": 5},
            {"course": course2, "user_id": 5, "rating": 4},
            # JavaScript course: ~3.8 average
            {"course": course3, "user_id": 1, "rating": 4},
            {"course": course3, "user_id": 2, "rating": 3},
            {"course": course3, "user_id": 3, "rating": 5},
            {"course": course3, "user_id": 4, "rating": 3},
            {"course": course3, "user_id": 5, "rating": 4},
            # TypeScript course: ~4.8 average
            {"course": course4, "user_id": 1, "rating": 5},
            {"course": course4, "user_id": 2, "rating": 5},
            {"course": course4, "user_id": 3, "rating": 5},
            {"course": course4, "user_id": 4, "rating": 4},
            {"course": course4, "user_id": 5, "rating": 5},
            # Vue.js course: ~4.0 average
            {"course": course5, "user_id": 1, "rating": 4},
            {"course": course5, "user_id": 2, "rating": 4},
            {"course": course5, "user_id": 3, "rating": 5},
            {"course": course5, "user_id": 4, "rating": 3},
            {"course": course5, "user_id": 5, "rating": 4},
            # Node.js course: ~4.4 average
            {"course": course6, "user_id": 1, "rating": 5},
            {"course": course6, "user_id": 2, "rating": 4},
            {"course": course6, "user_id": 3, "rating": 4},
            {"course": course6, "user_id": 4, "rating": 5},
            {"course": course6, "user_id": 5, "rating": 4},
            # Docker course: ~4.6 average
            {"course": course7, "user_id": 1, "rating": 5},
            {"course": course7, "user_id": 2, "rating": 5},
            {"course": course7, "user_id": 3, "rating": 4},
            {"course": course7, "user_id": 4, "rating": 5},
            {"course": course7, "user_id": 5, "rating": 4},
            # CSS course: ~3.6 average
            {"course": course8, "user_id": 1, "rating": 4},
            {"course": course8, "user_id": 2, "rating": 3},
            {"course": course8, "user_id": 3, "rating": 4},
            {"course": course8, "user_id": 4, "rating": 3},
            {"course": course8, "user_id": 5, "rating": 4},
            # Angular course: ~3.4 average
            {"course": course9, "user_id": 1, "rating": 4},
            {"course": course9, "user_id": 2, "rating": 3},
            {"course": course9, "user_id": 3, "rating": 3},
            {"course": course9, "user_id": 4, "rating": 4},
            {"course": course9, "user_id": 5, "rating": 3},
        ]

        for r in ratings_data:
            rating = CourseRating(
                course_id=r["course"].id,
                user_id=r["user_id"],
                rating=r["rating"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(rating)

        db.commit()

        all_courses = [course1, course2, course3, course4, course5, course6, course7, course8, course9]
        all_teachers = [teacher1, teacher2, teacher3, teacher4, teacher5, teacher6]
        print("✅ Sample data created successfully!")
        print(f"   - Created {len(all_teachers)} teachers")
        print(f"   - Created {len(all_courses)} courses")
        print(f"   - Created {len(lessons_data)} lessons")
        print(f"   - Created {len(ratings_data)} ratings")

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
        db.query(CourseRating).delete()
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
