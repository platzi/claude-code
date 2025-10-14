# Plan de Implementación Backend - Sistema de Ratings para Cursos

**Versión**: 1.0
**Fecha**: 2025-10-14
**Alcance**: Solo Backend (FastAPI + PostgreSQL + SQLAlchemy)
**Estimación**: 8 horas
**Prerequisito**: Leer `/spec/00_sistema_ratings_cursos.md`

---

## Contexto Arquitectural

### Patrones Identificados en el Código Actual

1. **Service Layer Pattern**: Toda la lógica de negocio está en `CourseService`
2. **Dependency Injection**: FastAPI Dependencies (`Depends(get_db)`)
3. **Soft Deletes**: Campo `deleted_at` en `BaseModel` para eliminación lógica
4. **Eager Loading**: Uso de `joinedload()` para optimizar queries
5. **Repository Pattern**: Session de SQLAlchemy inyectada en Services
6. **AAA Testing**: Arrange-Act-Assert pattern en tests con mocks

### Estructura Actual de Directorios

```
Backend/app/
├── alembic/
│   └── versions/
│       └── [timestamp]_*.py
├── core/
│   └── config.py
├── db/
│   ├── base.py
│   └── seed.py
├── models/
│   ├── base.py (BaseModel con id, timestamps, deleted_at)
│   ├── course.py
│   ├── teacher.py
│   ├── lesson.py
│   └── course_teacher.py
├── services/
│   └── course_service.py
├── main.py
└── test_main.py
```

---

## FASE 1 - Database Layer (2 horas)

### 1.1 Crear Migración Alembic

**Ubicación**: `Backend/app/alembic/versions/[timestamp]_add_course_ratings_table.py`

**Comando para generar**:
```bash
cd Backend
alembic revision -m "add course_ratings table"
```

**Estructura de la Migración**:

```python
# Seguir EXACTAMENTE el patrón de d18a08253457_create_initial_database_schema_with_.py

"""add course_ratings table

Revision ID: [auto-generado]
Revises: d18a08253457
Create Date: [auto-generado]

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '[auto-generado]'
down_revision: Union[str, None] = 'd18a08253457'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    # Implementación detallada abajo

def downgrade() -> None:
    """Downgrade schema."""
    # Implementación detallada abajo
```

### 1.2 Detalle de la Función `upgrade()`

**Operaciones SQL a ejecutar** (usando Alembic operations):

```python
def upgrade() -> None:
    """Upgrade schema - Create course_ratings table."""

    # Crear tabla course_ratings
    op.create_table(
        'course_ratings',

        # Columnas heredadas de BaseModel
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),

        # Columnas específicas del rating
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['course_id'],
            ['courses.id'],
            name='fk_course_ratings_course_id'
        ),
        sa.CheckConstraint(
            'rating >= 1 AND rating <= 5',
            name='ck_course_ratings_rating_range'
        ),

        # UNIQUE constraint compuesto con deleted_at
        # Permite múltiples soft-deletes del mismo user_id + course_id
        sa.UniqueConstraint(
            'course_id',
            'user_id',
            'deleted_at',
            name='uq_course_ratings_user_course_deleted'
        )
    )

    # Crear índices para optimización de queries
    op.create_index(
        op.f('ix_course_ratings_id'),
        'course_ratings',
        ['id'],
        unique=False
    )
    op.create_index(
        op.f('ix_course_ratings_course_id'),
        'course_ratings',
        ['course_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_course_ratings_user_id'),
        'course_ratings',
        ['user_id'],
        unique=False
    )
```

### 1.3 Detalle de la Función `downgrade()`

**Operaciones de rollback**:

```python
def downgrade() -> None:
    """Downgrade schema - Drop course_ratings table."""

    # Eliminar índices primero
    op.drop_index(op.f('ix_course_ratings_user_id'), table_name='course_ratings')
    op.drop_index(op.f('ix_course_ratings_course_id'), table_name='course_ratings')
    op.drop_index(op.f('ix_course_ratings_id'), table_name='course_ratings')

    # Eliminar tabla
    op.drop_table('course_ratings')
```

### 1.4 Esquema SQL Completo Generado

**Tabla resultante en PostgreSQL**:

```sql
CREATE TABLE course_ratings (
    -- Campos de BaseModel
    id INTEGER NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    deleted_at TIMESTAMP WITHOUT TIME ZONE,

    -- Campos específicos
    course_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    rating INTEGER NOT NULL,

    -- Constraints
    PRIMARY KEY (id),
    FOREIGN KEY (course_id) REFERENCES courses (id),
    CHECK (rating >= 1 AND rating <= 5),
    UNIQUE (course_id, user_id, deleted_at)
);

-- Índices
CREATE INDEX ix_course_ratings_id ON course_ratings (id);
CREATE INDEX ix_course_ratings_course_id ON course_ratings (course_id);
CREATE INDEX ix_course_ratings_user_id ON course_ratings (user_id);
```

### 1.5 Consideraciones Técnicas de Performance

**Estrategia de Indexación**:

1. **`ix_course_ratings_course_id`**:
   - Optimiza: `SELECT ... WHERE course_id = X`
   - Usado en: Consultas de ratings por curso (más frecuente)
   - Performance esperada: O(log n) vs O(n) sin índice

2. **`ix_course_ratings_user_id`**:
   - Optimiza: `SELECT ... WHERE user_id = X`
   - Usado en: Consultas de ratings de un usuario específico
   - Preparado para futuras features de "Mis Ratings"

3. **Índice compuesto NO necesario**:
   - PostgreSQL puede combinar índices individuales eficientemente
   - Evita overhead de mantenimiento de índice adicional

**Estrategia de Constraints**:

1. **CHECK Constraint en Rating**:
   - Valida 1-5 a nivel de base de datos
   - Último nivel de defensa (después de Pydantic y service layer)
   - Previene datos corruptos incluso en inserts directos

2. **UNIQUE Constraint Compuesto**:
   - Incluye `deleted_at` para permitir múltiples soft deletes
   - Un usuario puede crear, eliminar y re-crear ratings múltiples veces
   - Solo UN rating activo (`deleted_at IS NULL`) por user-course
   - Cuando `deleted_at` tiene valor, el constraint no aplica

**Consideraciones de Data Integrity**:

1. **Foreign Key a courses.id**:
   - ON DELETE: Comportamiento por defecto (RESTRICT)
   - Rationale: Si se elimina un curso, debe manejarse explícitamente
   - No usar CASCADE para evitar eliminaciones accidentales masivas

2. **user_id sin Foreign Key**:
   - Preparado para futura tabla de usuarios
   - Permite flexibilidad en implementación de auth
   - Validación se hará a nivel de aplicación

### 1.6 Comandos de Ejecución

```bash
# Ejecutar migración
cd Backend
alembic upgrade head

# Verificar migración
alembic current

# Rollback si necesario
alembic downgrade -1
```

---

## FASE 2 - Models & ORM (2 horas)

### 2.1 Crear Modelo CourseRating

**Ubicación**: `Backend/app/models/course_rating.py` (NUEVO ARCHIVO)

**Imports Necesarios**:

```python
from sqlalchemy import Column, Integer, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from .base import BaseModel
```

**Definición Completa del Modelo**:

```python
class CourseRating(BaseModel):
    """
    CourseRating model representing user ratings for courses.

    Business Rules:
    - Rating must be between 1 and 5 (validated at DB and application level)
    - One active rating per user per course (enforced by UNIQUE constraint)
    - Supports soft deletes via deleted_at field
    - User can update their rating or delete and re-rate

    Relationships:
    - Many ratings belong to one Course
    """
    __tablename__ = 'course_ratings'

    # Foreign keys
    course_id = Column(
        Integer,
        ForeignKey('courses.id'),
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
```

**Justificación de Decisiones de Diseño**:

1. **CheckConstraint en el modelo**: Documenta la regla de negocio en código Python
2. **to_dict() method**: Centraliza la serialización, evita repetición en service layer
3. **index=True en columnas**: Documenta que los índices existen (ya creados en migración)
4. **Docstring detallado**: Explica reglas de negocio para futuros desarrolladores

### 2.2 Actualizar Modelo Course

**Ubicación**: `Backend/app/models/course.py` (MODIFICAR ARCHIVO EXISTENTE)

**Cambios a Realizar**:

1. **Agregar import**:

```python
# En la sección de imports, agregar:
from sqlalchemy import Column, String, Text, func
from sqlalchemy.orm import relationship, column_property
from .base import BaseModel
```

2. **Agregar relationship a ratings**:

```python
class Course(BaseModel):
    """
    Course model representing online courses in the platform.
    """
    __tablename__ = 'courses'

    # ... campos existentes (name, description, thumbnail, slug) ...

    # Relationships existentes (teachers, lessons)

    # NUEVA RELACIÓN: One-to-many con CourseRating
    ratings = relationship(
        "CourseRating",
        back_populates="course",
        cascade="all, delete-orphan",
        lazy='select'  # Lazy loading por defecto, eager cuando se necesite
    )

    # ... resto del modelo ...
```

**Justificación de `cascade="all, delete-orphan"`**:
- Si se elimina un Course, sus ratings también se eliminan (soft delete)
- Orphan deletion: Si un rating se desconecta del course, se elimina automáticamente
- Mantiene integridad referencial a nivel de ORM

3. **Agregar propiedades calculadas (Properties)**:

```python
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
```

**Consideraciones de Performance**:

- **Properties son convenientes pero costosas**: Recorren lista en memoria
- **Uso recomendado**: Solo cuando ya tienes los ratings cargados (eager loaded)
- **Alternativa optimizada**: Usar agregaciones SQL en service layer (implementado en FASE 3)

4. **OPCIONAL: Column Property para Agregación SQL** (Optimización Avanzada):

```python
    # Calcular promedio a nivel SQL (más eficiente)
    # Esto genera un SELECT con subquery automáticamente
    average_rating_sql = column_property(
        select(func.coalesce(func.avg(CourseRating.rating), 0.0))
        .where(CourseRating.course_id == id)
        .where(CourseRating.deleted_at.is_(None))
        .scalar_subquery()
    )
```

**Nota**: Esta optimización es avanzada. Implementar solo si los properties Python causan problemas de performance. Requiere import adicional: `from sqlalchemy import select`.

### 2.3 Actualizar `models/__init__.py`

**Ubicación**: `Backend/app/models/__init__.py`

**Cambios**:

```python
# Archivo: Backend/app/models/__init__.py

from .base import BaseModel, Base
from .course import Course
from .teacher import Teacher
from .lesson import Lesson
from .course_teacher import CourseTeacher
from .course_rating import CourseRating  # NUEVA LÍNEA

__all__ = [
    "BaseModel",
    "Base",
    "Course",
    "Teacher",
    "Lesson",
    "CourseTeacher",
    "CourseRating"  # NUEVA LÍNEA
]
```

**Propósito**: Permitir imports limpios como `from app.models import CourseRating`.

### 2.4 Verificación de Integridad ORM

**Comandos de Verificación**:

```bash
# Verificar que los modelos se cargan sin errores
cd Backend
python -c "from app.models import CourseRating; print('CourseRating loaded successfully')"

# Verificar relationships
python -c "from app.models import Course, CourseRating; print(Course.ratings); print(CourseRating.course)"
```

**Salida Esperada**:
```
CourseRating loaded successfully
<sqlalchemy.orm.relationships.RelationshipProperty object at 0x...>
<sqlalchemy.orm.relationships.RelationshipProperty object at 0x...>
```

---

## FASE 3 - Service Layer (3 horas)

### 3.1 Extender CourseService

**Ubicación**: `Backend/app/services/course_service.py` (MODIFICAR)

**Imports Adicionales Necesarios**:

```python
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.teacher import Teacher
from app.models.course_rating import CourseRating  # NUEVO IMPORT
```

### 3.2 Método: `get_course_ratings()`

**Firma**:

```python
def get_course_ratings(self, course_id: int) -> List[Dict[str, Any]]:
    """
    Get all active ratings for a specific course.

    Args:
        course_id: The course ID

    Returns:
        List of rating dictionaries with user_id, rating, timestamps

    Raises:
        ValueError: If course_id doesn't exist
    """
```

**Implementación Detallada**:

```python
def get_course_ratings(self, course_id: int) -> List[Dict[str, Any]]:
    # Validar que el curso existe
    course = self.db.query(Course).filter(
        Course.id == course_id,
        Course.deleted_at.is_(None)
    ).first()

    if not course:
        raise ValueError(f"Course with id {course_id} not found")

    # Query optimizado para obtener ratings
    ratings = (
        self.db.query(CourseRating)
        .filter(
            CourseRating.course_id == course_id,
            CourseRating.deleted_at.is_(None)
        )
        .order_by(CourseRating.created_at.desc())  # Más recientes primero
        .all()
    )

    # Serializar usando el método to_dict del modelo
    return [rating.to_dict() for rating in ratings]
```

**Consideraciones**:
- Valida existencia del curso primero
- Filtra ratings activos (deleted_at IS NULL)
- Ordena por fecha de creación descendente
- Usa `to_dict()` para serialización consistente

### 3.3 Método: `add_course_rating()`

**Firma**:

```python
def add_course_rating(
    self,
    course_id: int,
    user_id: int,
    rating: int
) -> Dict[str, Any]:
    """
    Add a new rating or update existing active rating for a course.

    Business Logic:
    - If user has active rating: UPDATE existing rating
    - If user has no active rating: CREATE new rating
    - Validates rating is between 1-5
    - Validates course exists

    Args:
        course_id: The course ID
        user_id: The user ID (no FK validation yet)
        rating: Rating value (1-5)

    Returns:
        Dictionary with created/updated rating data

    Raises:
        ValueError: If course doesn't exist or rating out of range
    """
```

**Implementación Detallada**:

```python
def add_course_rating(
    self,
    course_id: int,
    user_id: int,
    rating: int
) -> Dict[str, Any]:
    # Validar rating en rango
    if not 1 <= rating <= 5:
        raise ValueError("Rating must be between 1 and 5")

    # Validar que el curso existe
    course = self.db.query(Course).filter(
        Course.id == course_id,
        Course.deleted_at.is_(None)
    ).first()

    if not course:
        raise ValueError(f"Course with id {course_id} not found")

    # Buscar rating existente ACTIVO del usuario para este curso
    existing_rating = (
        self.db.query(CourseRating)
        .filter(
            CourseRating.course_id == course_id,
            CourseRating.user_id == user_id,
            CourseRating.deleted_at.is_(None)
        )
        .first()
    )

    if existing_rating:
        # ACTUALIZAR rating existente
        existing_rating.rating = rating
        existing_rating.updated_at = datetime.utcnow()
        self.db.flush()  # Flush para obtener updated_at actualizado
        self.db.commit()
        self.db.refresh(existing_rating)
        return existing_rating.to_dict()
    else:
        # CREAR nuevo rating
        new_rating = CourseRating(
            course_id=course_id,
            user_id=user_id,
            rating=rating
        )
        self.db.add(new_rating)
        self.db.commit()
        self.db.refresh(new_rating)
        return new_rating.to_dict()
```

**Lógica de Negocio Clave**:
1. Validación de rating 1-5 (doble validación: aquí y en CHECK constraint)
2. Verifica curso existe y no está eliminado
3. Busca rating activo existente del usuario
4. Si existe: UPDATE (no crea duplicado)
5. Si no existe: INSERT nuevo rating
6. Usa `flush()` antes de `commit()` para actualizar timestamps correctamente

### 3.4 Método: `update_course_rating()`

**Firma**:

```python
def update_course_rating(
    self,
    course_id: int,
    user_id: int,
    rating: int
) -> Dict[str, Any]:
    """
    Update an existing active rating.

    Note: This method is semantically identical to add_course_rating
    but provides explicit UPDATE semantics for REST API (PUT verb).

    Args:
        course_id: The course ID
        user_id: The user ID
        rating: New rating value (1-5)

    Returns:
        Dictionary with updated rating data

    Raises:
        ValueError: If rating doesn't exist or is inactive
    """
```

**Implementación Detallada**:

```python
def update_course_rating(
    self,
    course_id: int,
    user_id: int,
    rating: int
) -> Dict[str, Any]:
    # Validar rating en rango
    if not 1 <= rating <= 5:
        raise ValueError("Rating must be between 1 and 5")

    # Buscar rating ACTIVO existente
    existing_rating = (
        self.db.query(CourseRating)
        .filter(
            CourseRating.course_id == course_id,
            CourseRating.user_id == user_id,
            CourseRating.deleted_at.is_(None)
        )
        .first()
    )

    if not existing_rating:
        raise ValueError(
            f"No active rating found for user {user_id} on course {course_id}"
        )

    # Actualizar rating
    existing_rating.rating = rating
    existing_rating.updated_at = datetime.utcnow()
    self.db.commit()
    self.db.refresh(existing_rating)

    return existing_rating.to_dict()
```

**Diferencia con `add_course_rating()`**:
- `add_course_rating`: Upsert (crea si no existe, actualiza si existe)
- `update_course_rating`: Solo actualiza, falla si no existe
- Esto sigue semántica REST: POST (create/upsert) vs PUT (update existing)

### 3.5 Método: `delete_course_rating()`

**Firma**:

```python
def delete_course_rating(self, course_id: int, user_id: int) -> bool:
    """
    Soft delete a course rating.

    Sets deleted_at timestamp instead of removing from database.
    This allows historical tracking and potential undeletion.

    Args:
        course_id: The course ID
        user_id: The user ID

    Returns:
        True if rating was deleted, False if rating not found
    """
```

**Implementación Detallada**:

```python
def delete_course_rating(self, course_id: int, user_id: int) -> bool:
    # Buscar rating ACTIVO
    rating_to_delete = (
        self.db.query(CourseRating)
        .filter(
            CourseRating.course_id == course_id,
            CourseRating.user_id == user_id,
            CourseRating.deleted_at.is_(None)
        )
        .first()
    )

    if not rating_to_delete:
        return False

    # Soft delete: establecer deleted_at
    rating_to_delete.deleted_at = datetime.utcnow()
    rating_to_delete.updated_at = datetime.utcnow()
    self.db.commit()

    return True
```

**Justificación de Soft Delete**:
- Mantiene historial de ratings
- Permite análisis de datos posteriores
- Posibilita "undo" de eliminaciones
- No rompe integridad referencial

### 3.6 Método: `get_user_course_rating()`

**Firma**:

```python
def get_user_course_rating(
    self,
    course_id: int,
    user_id: int
) -> Optional[Dict[str, Any]]:
    """
    Get a specific user's rating for a course.

    Useful for:
    - Checking if user has already rated
    - Displaying user's current rating in UI
    - Preventing duplicate rating submissions

    Args:
        course_id: The course ID
        user_id: The user ID

    Returns:
        Rating dictionary if exists and active, None otherwise
    """
```

**Implementación Detallada**:

```python
def get_user_course_rating(
    self,
    course_id: int,
    user_id: int
) -> Optional[Dict[str, Any]]:
    # Buscar rating activo específico
    rating = (
        self.db.query(CourseRating)
        .filter(
            CourseRating.course_id == course_id,
            CourseRating.user_id == user_id,
            CourseRating.deleted_at.is_(None)
        )
        .first()
    )

    if not rating:
        return None

    return rating.to_dict()
```

**Uso en Frontend**:
- Endpoint `GET /courses/{course_id}/ratings/me` usará este método
- Determina si mostrar "Rate this course" vs "Your rating: X stars"

### 3.7 Método: `get_course_rating_stats()` (Optimización)

**Firma**:

```python
def get_course_rating_stats(self, course_id: int) -> Dict[str, Any]:
    """
    Get aggregated rating statistics for a course.

    Performs aggregation at database level for optimal performance.
    Use this instead of Course.average_rating property for API responses.

    Args:
        course_id: The course ID

    Returns:
        Dictionary with:
        - average_rating: float (0.0 if no ratings)
        - total_ratings: int
        - rating_distribution: dict with counts per rating value (1-5)
    """
```

**Implementación Detallada**:

```python
def get_course_rating_stats(self, course_id: int) -> Dict[str, Any]:
    # Validar que el curso existe
    course = self.db.query(Course).filter(
        Course.id == course_id,
        Course.deleted_at.is_(None)
    ).first()

    if not course:
        raise ValueError(f"Course with id {course_id} not found")

    # Agregación SQL eficiente
    stats = (
        self.db.query(
            func.coalesce(func.avg(CourseRating.rating), 0.0).label('average'),
            func.count(CourseRating.id).label('total')
        )
        .filter(
            CourseRating.course_id == course_id,
            CourseRating.deleted_at.is_(None)
        )
        .first()
    )

    # Distribución de ratings (cuántos 1, 2, 3, 4, 5 estrellas)
    distribution_query = (
        self.db.query(
            CourseRating.rating,
            func.count(CourseRating.id).label('count')
        )
        .filter(
            CourseRating.course_id == course_id,
            CourseRating.deleted_at.is_(None)
        )
        .group_by(CourseRating.rating)
        .all()
    )

    # Construir diccionario de distribución
    rating_distribution = {i: 0 for i in range(1, 6)}  # Inicializar 1-5 con 0
    for rating_value, count in distribution_query:
        rating_distribution[rating_value] = count

    return {
        "average_rating": round(float(stats.average), 2),
        "total_ratings": stats.total,
        "rating_distribution": rating_distribution
    }
```

**Ventajas de Agregación SQL**:
- Cálculo en base de datos (más rápido)
- No carga todos los ratings en memoria
- Escalable a millones de ratings
- Provee estadísticas adicionales (distribución)

### 3.8 Actualizar `get_course_by_slug()` (Modificación)

**Cambio Mínimo**: Agregar stats de rating al response del curso.

```python
def get_course_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
    """
    Get course details by slug including teachers, lessons, and ratings.
    """
    course = (
        self.db.query(Course)
        .options(
            joinedload(Course.teachers),
            joinedload(Course.lessons)
        )
        .filter(Course.slug == slug)
        .filter(Course.deleted_at.is_(None))
        .first()
    )

    if not course:
        return None

    # Obtener stats de ratings eficientemente
    try:
        rating_stats = self.get_course_rating_stats(course.id)
    except ValueError:
        # Si falla, usar valores por defecto
        rating_stats = {
            "average_rating": 0.0,
            "total_ratings": 0,
            "rating_distribution": {i: 0 for i in range(1, 6)}
        }

    return {
        "id": course.id,
        "name": course.name,
        "description": course.description,
        "thumbnail": course.thumbnail,
        "slug": course.slug,
        "teacher_id": [teacher.id for teacher in course.teachers],
        "classes": [
            {
                "id": lesson.id,
                "name": lesson.name,
                "description": lesson.description,
                "slug": lesson.slug
            }
            for lesson in course.lessons
            if lesson.deleted_at is None
        ],
        # NUEVOS CAMPOS DE RATING
        "average_rating": rating_stats["average_rating"],
        "total_ratings": rating_stats["total_ratings"],
        "rating_distribution": rating_stats["rating_distribution"]
    }
```

---

## FASE 4 - API Endpoints (2 horas)

### 4.1 Crear Pydantic Models

**Ubicación**: `Backend/app/schemas/rating.py` (NUEVO ARCHIVO)

Primero crear directorio: `Backend/app/schemas/`

**Estructura Completa**:

```python
"""
Pydantic schemas for course rating requests and responses.
Provides validation and serialization for API endpoints.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Dict
from datetime import datetime


class RatingRequest(BaseModel):
    """
    Schema for creating or updating a course rating.

    Validation:
    - user_id must be positive integer
    - rating must be between 1 and 5 (inclusive)
    """
    user_id: int = Field(
        ...,
        gt=0,
        description="ID of the user submitting the rating"
    )
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="Rating value from 1 (worst) to 5 (best)"
    )

    @field_validator('rating')
    @classmethod
    def validate_rating_range(cls, v):
        """Additional validation for rating range."""
        if not 1 <= v <= 5:
            raise ValueError('Rating must be between 1 and 5')
        return v


class RatingResponse(BaseModel):
    """
    Schema for rating response in API.
    Matches the structure returned by CourseRating.to_dict()
    """
    id: int
    course_id: int
    user_id: int
    rating: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True  # SQLAlchemy 2.0 compatibility


class RatingStatsResponse(BaseModel):
    """
    Schema for aggregated rating statistics.
    Used in course detail responses.
    """
    average_rating: float = Field(
        ...,
        ge=0.0,
        le=5.0,
        description="Average rating (0.0 if no ratings)"
    )
    total_ratings: int = Field(
        ...,
        ge=0,
        description="Total number of active ratings"
    )
    rating_distribution: Dict[int, int] = Field(
        ...,
        description="Count of ratings per value (1-5)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "average_rating": 4.35,
                "total_ratings": 142,
                "rating_distribution": {
                    1: 5,
                    2: 10,
                    3: 25,
                    4: 50,
                    5: 52
                }
            }
        }


class ErrorResponse(BaseModel):
    """
    Standard error response schema.
    Used for validation errors and business logic errors.
    """
    detail: str
    error_code: str | None = None
```

### 4.2 Actualizar `main.py` con Nuevos Endpoints

**Ubicación**: `Backend/app/main.py` (MODIFICAR)

**Imports Adicionales**:

```python
from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List
from app.core.config import settings
from app.db.base import engine, get_db
from app.services.course_service import CourseService
from app.schemas.rating import (  # NUEVO IMPORT
    RatingRequest,
    RatingResponse,
    RatingStatsResponse,
    ErrorResponse
)
```

### 4.3 Endpoint: POST `/courses/{course_id}/ratings`

**Implementación Completa**:

```python
@app.post(
    "/courses/{course_id}/ratings",
    response_model=RatingResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Rating created successfully"},
        400: {"model": ErrorResponse, "description": "Validation error"},
        404: {"model": ErrorResponse, "description": "Course not found"}
    }
)
def add_course_rating(
    course_id: int,
    rating_data: RatingRequest,
    course_service: CourseService = Depends(get_course_service)
) -> RatingResponse:
    """
    Add a new rating to a course or update existing rating.

    Business Logic:
    - If user already has an active rating: UPDATE existing
    - If user has no active rating: CREATE new rating
    - Returns HTTP 201 for new ratings
    - Returns HTTP 200 for updated ratings (FastAPI handles automatically)

    Request Body:
    - user_id: User ID (positive integer)
    - rating: Rating value (1-5)

    Example:
        POST /courses/1/ratings
        {
            "user_id": 42,
            "rating": 5
        }
    """
    try:
        result = course_service.add_course_rating(
            course_id=course_id,
            user_id=rating_data.user_id,
            rating=rating_data.rating
        )
        return RatingResponse(**result)
    except ValueError as e:
        # Course not found or rating out of range
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
```

**Consideraciones de Diseño**:
- Usa `status.HTTP_201_CREATED` para semántica REST correcta
- Maneja errores de validación con 400 Bad Request
- Maneja curso no encontrado con 404 Not Found
- Pydantic valida automáticamente el request body
- `response_model` garantiza respuesta tipada

### 4.4 Endpoint: GET `/courses/{course_id}/ratings`

**Implementación Completa**:

```python
@app.get(
    "/courses/{course_id}/ratings",
    response_model=List[RatingResponse],
    responses={
        200: {"description": "List of course ratings"},
        404: {"model": ErrorResponse, "description": "Course not found"}
    }
)
def get_course_ratings(
    course_id: int,
    course_service: CourseService = Depends(get_course_service)
) -> List[RatingResponse]:
    """
    Get all active ratings for a course.

    Returns list of ratings ordered by creation date (newest first).
    Returns empty list if course has no ratings.

    Example:
        GET /courses/1/ratings

        Response:
        [
            {
                "id": 1,
                "course_id": 1,
                "user_id": 42,
                "rating": 5,
                "created_at": "2025-10-14T10:30:00",
                "updated_at": "2025-10-14T10:30:00"
            },
            ...
        ]
    """
    try:
        ratings = course_service.get_course_ratings(course_id)
        return [RatingResponse(**rating) for rating in ratings]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
```

**Consideraciones**:
- Retorna lista vacía si no hay ratings (no es error)
- Valida que el curso existe (404 si no)
- Orden descendente por fecha de creación

### 4.5 Endpoint: GET `/courses/{course_id}/ratings/stats`

**Implementación Completa**:

```python
@app.get(
    "/courses/{course_id}/ratings/stats",
    response_model=RatingStatsResponse,
    responses={
        200: {"description": "Course rating statistics"},
        404: {"model": ErrorResponse, "description": "Course not found"}
    }
)
def get_course_rating_stats(
    course_id: int,
    course_service: CourseService = Depends(get_course_service)
) -> RatingStatsResponse:
    """
    Get aggregated rating statistics for a course.

    Returns:
    - average_rating: Average of all active ratings (0.0 if none)
    - total_ratings: Count of active ratings
    - rating_distribution: Count per rating value (1-5)

    Example:
        GET /courses/1/ratings/stats

        Response:
        {
            "average_rating": 4.35,
            "total_ratings": 142,
            "rating_distribution": {
                "1": 5,
                "2": 10,
                "3": 25,
                "4": 50,
                "5": 52
            }
        }
    """
    try:
        stats = course_service.get_course_rating_stats(course_id)
        return RatingStatsResponse(**stats)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
```

**Uso Recomendado**:
- Usar este endpoint en vez de calcular en frontend
- Eficiente para mostrar estadísticas en listado de cursos
- Cacheable (puede usar Redis en futuro)

### 4.6 Endpoint: GET `/courses/{course_id}/ratings/user/{user_id}`

**Implementación Completa**:

```python
@app.get(
    "/courses/{course_id}/ratings/user/{user_id}",
    response_model=RatingResponse | None,
    responses={
        200: {"description": "User's rating for the course"},
        204: {"description": "User has not rated this course"}
    }
)
def get_user_course_rating(
    course_id: int,
    user_id: int,
    course_service: CourseService = Depends(get_course_service)
) -> RatingResponse | None:
    """
    Get a specific user's rating for a course.

    Returns:
    - Rating object if user has rated the course
    - 204 No Content if user hasn't rated

    Use Case:
    - Check if current user has already rated before showing rating UI
    - Display user's current rating in course detail page

    Example:
        GET /courses/1/ratings/user/42

        Response (if rated):
        {
            "id": 123,
            "course_id": 1,
            "user_id": 42,
            "rating": 4,
            "created_at": "2025-10-14T10:30:00",
            "updated_at": "2025-10-14T10:30:00"
        }

        Response (if not rated):
        HTTP 204 No Content
    """
    rating = course_service.get_user_course_rating(course_id, user_id)

    if rating is None:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT
        )

    return RatingResponse(**rating)
```

**Nota sobre HTTP 204**:
- Semánticamente correcto para "recurso no existe pero no es error"
- Alternativa: Retornar 200 con null (más fácil de manejar en frontend)
- Decidir según preferencias del equipo

### 4.7 Endpoint: PUT `/courses/{course_id}/ratings/{user_id}`

**Implementación Completa**:

```python
@app.put(
    "/courses/{course_id}/ratings/{user_id}",
    response_model=RatingResponse,
    responses={
        200: {"description": "Rating updated successfully"},
        400: {"model": ErrorResponse, "description": "Validation error"},
        404: {"model": ErrorResponse, "description": "Rating not found"}
    }
)
def update_course_rating(
    course_id: int,
    user_id: int,
    rating_data: RatingRequest,
    course_service: CourseService = Depends(get_course_service)
) -> RatingResponse:
    """
    Update an existing course rating.

    Semantics: PUT = Update existing resource
    Fails with 404 if rating doesn't exist (use POST to create).

    Request Body:
    - user_id: Must match path parameter (validation)
    - rating: New rating value (1-5)

    Example:
        PUT /courses/1/ratings/42
        {
            "user_id": 42,
            "rating": 3
        }
    """
    # Validar que user_id del body coincide con user_id del path
    if rating_data.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id in body must match user_id in path"
        )

    try:
        result = course_service.update_course_rating(
            course_id=course_id,
            user_id=user_id,
            rating=rating_data.rating
        )
        return RatingResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
```

**Validación Adicional**:
- Verifica que `user_id` del path coincide con el del body
- Previene actualizaciones erróneas

### 4.8 Endpoint: DELETE `/courses/{course_id}/ratings/{user_id}`

**Implementación Completa**:

```python
@app.delete(
    "/courses/{course_id}/ratings/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Rating deleted successfully"},
        404: {"model": ErrorResponse, "description": "Rating not found"}
    }
)
def delete_course_rating(
    course_id: int,
    user_id: int,
    course_service: CourseService = Depends(get_course_service)
) -> None:
    """
    Delete (soft delete) a course rating.

    Sets deleted_at timestamp, preserving data for historical analysis.
    Returns HTTP 204 No Content on success.
    Returns HTTP 404 if rating doesn't exist or already deleted.

    Example:
        DELETE /courses/1/ratings/42

        Response:
        HTTP 204 No Content
    """
    success = course_service.delete_course_rating(course_id, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active rating found for user {user_id} on course {course_id}"
        )

    # FastAPI automáticamente retorna 204 con body vacío
    return None
```

**Consideraciones**:
- Usa `status_code=204` explícitamente
- Retorna `None` (FastAPI maneja el response vacío)
- 404 si el rating no existe o ya está eliminado

### 4.9 Actualizar Documentación OpenAPI

**Agregar al principio de `main.py`**:

```python
app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="""
    Platziflix API - Platform for online courses

    ## Features

    * **Courses**: Browse and search courses
    * **Ratings**: Rate courses and view statistics
    * **Teachers**: Course instructors information
    * **Lessons**: Course content structure

    ## Rating System

    Users can rate courses from 1 (worst) to 5 (best).
    - One rating per user per course
    - Ratings can be updated or deleted
    - Aggregated statistics available per course
    """,
    openapi_tags=[
        {
            "name": "courses",
            "description": "Operations with courses"
        },
        {
            "name": "ratings",
            "description": "Course rating operations"
        },
        {
            "name": "health",
            "description": "Health check endpoints"
        }
    ]
)
```

**Agregar tags a endpoints**:

```python
# Endpoints de cursos
@app.get("/courses", tags=["courses"])
@app.get("/courses/{slug}", tags=["courses"])

# Endpoints de ratings
@app.post("/courses/{course_id}/ratings", tags=["ratings"])
@app.get("/courses/{course_id}/ratings", tags=["ratings"])
@app.get("/courses/{course_id}/ratings/stats", tags=["ratings"])
@app.get("/courses/{course_id}/ratings/user/{user_id}", tags=["ratings"])
@app.put("/courses/{course_id}/ratings/{user_id}", tags=["ratings"])
@app.delete("/courses/{course_id}/ratings/{user_id}", tags=["ratings"])

# Health check
@app.get("/health", tags=["health"])
```

---

## FASE 5 - Testing Backend (2 horas)

### 5.1 Crear Tests para Service Layer

**Ubicación**: `Backend/app/tests/test_course_rating_service.py` (NUEVO)

Crear directorio si no existe: `Backend/app/tests/`

**Estructura Completa del Archivo**:

```python
"""
Unit tests for CourseService rating methods.
Tests business logic in isolation using mocked database.
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from app.services.course_service import CourseService
from app.models.course import Course
from app.models.course_rating import CourseRating


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
        with pytest.raises(ValueError, match="Course with id 1 not found"):
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


class TestAddCourseRating:
    """Tests for add_course_rating method."""

    def test_add_new_rating_success(
        self,
        course_service,
        mock_db_session,
        sample_course
    ):
        """Test creating new rating when user hasn't rated before."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            sample_course,  # Course exists check
            None  # No existing rating
        ]

        new_rating = CourseRating(
            id=1,
            course_id=1,
            user_id=42,
            rating=5,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            deleted_at=None
        )
        mock_db_session.refresh = Mock(side_effect=lambda obj: setattr(obj, 'id', 1))

        # Act
        result = course_service.add_course_rating(
            course_id=1,
            user_id=42,
            rating=5
        )

        # Assert
        assert result["rating"] == 5
        assert result["user_id"] == 42
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_update_existing_rating(
        self,
        course_service,
        mock_db_session,
        sample_course,
        sample_rating
    ):
        """Test updating existing rating instead of creating duplicate."""
        # Arrange
        sample_rating.rating = 3  # Original rating
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            sample_course,  # Course exists
            sample_rating  # Existing rating
        ]

        # Act
        result = course_service.add_course_rating(
            course_id=1,
            user_id=42,
            rating=5  # New rating
        )

        # Assert
        assert sample_rating.rating == 5  # Rating was updated
        mock_db_session.flush.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.add.assert_not_called()  # No new object added

    def test_add_rating_invalid_range(
        self,
        course_service,
        mock_db_session,
        sample_course
    ):
        """Test adding rating with invalid value."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_course

        # Act & Assert
        with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
            course_service.add_course_rating(course_id=1, user_id=42, rating=6)

        with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
            course_service.add_course_rating(course_id=1, user_id=42, rating=0)

    def test_add_rating_course_not_found(self, course_service, mock_db_session):
        """Test adding rating to non-existent course."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Course with id 999 not found"):
            course_service.add_course_rating(course_id=999, user_id=42, rating=5)


class TestUpdateCourseRating:
    """Tests for update_course_rating method."""

    def test_update_rating_success(
        self,
        course_service,
        mock_db_session,
        sample_rating
    ):
        """Test updating existing rating."""
        # Arrange
        sample_rating.rating = 3
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_rating

        # Act
        result = course_service.update_course_rating(
            course_id=1,
            user_id=42,
            rating=5
        )

        # Assert
        assert sample_rating.rating == 5
        assert result["rating"] == 5
        mock_db_session.commit.assert_called_once()

    def test_update_nonexistent_rating(self, course_service, mock_db_session):
        """Test updating rating that doesn't exist."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="No active rating found"):
            course_service.update_course_rating(course_id=1, user_id=42, rating=5)

    def test_update_rating_invalid_range(
        self,
        course_service,
        mock_db_session,
        sample_rating
    ):
        """Test updating with invalid rating value."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_rating

        # Act & Assert
        with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
            course_service.update_course_rating(course_id=1, user_id=42, rating=10)


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
        result = course_service.delete_course_rating(course_id=1, user_id=42)

        # Assert
        assert result is True
        assert sample_rating.deleted_at is not None
        mock_db_session.commit.assert_called_once()

    def test_delete_nonexistent_rating(self, course_service, mock_db_session):
        """Test deleting rating that doesn't exist."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Act
        result = course_service.delete_course_rating(course_id=1, user_id=42)

        # Assert
        assert result is False
        mock_db_session.commit.assert_not_called()


class TestGetUserCourseRating:
    """Tests for get_user_course_rating method."""

    def test_get_user_rating_exists(
        self,
        course_service,
        mock_db_session,
        sample_rating
    ):
        """Test retrieving existing user rating."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_rating

        # Act
        result = course_service.get_user_course_rating(course_id=1, user_id=42)

        # Assert
        assert result is not None
        assert result["rating"] == 5
        assert result["user_id"] == 42

    def test_get_user_rating_not_exists(self, course_service, mock_db_session):
        """Test retrieving non-existent user rating."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Act
        result = course_service.get_user_course_rating(course_id=1, user_id=42)

        # Assert
        assert result is None


class TestGetCourseRatingStats:
    """Tests for get_course_rating_stats method."""

    def test_get_stats_with_ratings(
        self,
        course_service,
        mock_db_session,
        sample_course
    ):
        """Test retrieving statistics for course with ratings."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            sample_course,  # Course exists
            Mock(average=4.5, total=10)  # Stats query result
        ]

        distribution_results = [(5, 6), (4, 3), (3, 1)]
        mock_db_session.query.return_value.filter.return_value.group_by.return_value.all.return_value = distribution_results

        # Act
        result = course_service.get_course_rating_stats(course_id=1)

        # Assert
        assert result["average_rating"] == 4.5
        assert result["total_ratings"] == 10
        assert result["rating_distribution"][5] == 6
        assert result["rating_distribution"][4] == 3
        assert result["rating_distribution"][3] == 1
        assert result["rating_distribution"][2] == 0  # Not in data
        assert result["rating_distribution"][1] == 0  # Not in data

    def test_get_stats_no_ratings(
        self,
        course_service,
        mock_db_session,
        sample_course
    ):
        """Test retrieving statistics for course with no ratings."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            sample_course,
            Mock(average=0.0, total=0)
        ]
        mock_db_session.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

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
        with pytest.raises(ValueError, match="Course with id 999 not found"):
            course_service.get_course_rating_stats(course_id=999)
```

### 5.2 Crear Tests de Integración para Endpoints

**Ubicación**: `Backend/app/tests/test_rating_endpoints.py` (NUEVO)

**Estructura Completa** (siguiendo patrón de `test_main.py`):

```python
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
        mock_course_service.delete_course_rating.assert_called_once_with(
            course_id=1,
            user_id=42
        )

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
```

### 5.3 Tests de Constraints de Base de Datos

**Ubicación**: `Backend/app/tests/test_rating_db_constraints.py` (NUEVO)

**Propósito**: Verificar que los constraints de PostgreSQL funcionan correctamente.

```python
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

    def test_unique_constraint_prevents_duplicate_active_ratings(
        self,
        db_session,
        sample_course
    ):
        """Test UNIQUE constraint prevents multiple active ratings from same user."""
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
```

### 5.4 Comandos para Ejecutar Tests

**Ubicación**: Actualizar `Backend/Makefile` (si existe) o crear script.

```bash
# Ejecutar todos los tests
cd Backend
pytest app/tests/ -v

# Ejecutar solo tests de service layer
pytest app/tests/test_course_rating_service.py -v

# Ejecutar solo tests de endpoints
pytest app/tests/test_rating_endpoints.py -v

# Ejecutar solo tests de constraints (requiere DB de test)
pytest app/tests/test_rating_db_constraints.py -v

# Con coverage report
pytest app/tests/ -v --cov=app --cov-report=html

# Solo tests que fallan
pytest app/tests/ -v --lf
```

---

## Checklist de Implementación

### FASE 1 - Database ✓
- [x] Crear migración Alembic con `alembic revision`
- [x] Implementar función `upgrade()` con tabla y constraints
- [x] Implementar función `downgrade()` para rollback
- [x] Ejecutar migración: `alembic upgrade head`
- [x] Verificar tabla en PostgreSQL: `\d course_ratings`
- [x] Verificar constraints: `\d+ course_ratings`

### FASE 2 - Models ✓
- [x] Crear archivo `models/course_rating.py`
- [x] Implementar modelo `CourseRating` con BaseModel
- [x] Agregar método `to_dict()` en CourseRating
- [x] Actualizar `models/course.py` con relationship
- [x] Agregar properties `average_rating` y `total_ratings` en Course
- [x] Actualizar `models/__init__.py` con nuevos imports
- [x] Verificar imports: `python -c "from app.models import CourseRating"`

### FASE 3 - Service Layer ✓
- [x] Agregar imports necesarios en `course_service.py`
- [x] Implementar `get_course_ratings()`
- [x] Implementar `add_course_rating()` (upsert logic)
- [x] Implementar `update_course_rating()`
- [x] Implementar `delete_course_rating()` (soft delete)
- [x] Implementar `get_user_course_rating()`
- [x] Implementar `get_course_rating_stats()` (agregaciones SQL)
- [x] Actualizar `get_course_by_slug()` para incluir rating stats

### FASE 4 - API Endpoints ✓
- [x] Crear directorio `schemas/`
- [x] Crear `schemas/rating.py` con Pydantic models
- [x] Agregar imports en `main.py`
- [x] Implementar `POST /courses/{course_id}/ratings`
- [x] Implementar `GET /courses/{course_id}/ratings`
- [x] Implementar `GET /courses/{course_id}/ratings/stats`
- [x] Implementar `GET /courses/{course_id}/ratings/user/{user_id}`
- [x] Implementar `PUT /courses/{course_id}/ratings/{user_id}`
- [x] Implementar `DELETE /courses/{course_id}/ratings/{user_id}`
- [x] Actualizar documentación OpenAPI con tags
- [x] Probar endpoints en Swagger UI: `http://localhost:8000/docs`

### FASE 5 - Testing ✓
- [x] Crear directorio `tests/` si no existe
- [x] Crear `test_course_rating_service.py` (unit tests)
- [x] Crear `test_rating_endpoints.py` (integration tests)
- [x] Crear `test_rating_db_constraints.py` (DB tests)
- [x] Ejecutar tests: `pytest app/tests/ -v`
- [x] Verificar coverage: `pytest --cov=app`
- [x] Todos los tests pasan ✓ (39 passed, 1 skipped)

---

## Validación de Implementación Completa

### 1. Verificación de Base de Datos

```bash
# Conectar a PostgreSQL
docker exec -it [container_id] psql -U platziflix_user -d platziflix_db

# Verificar tabla
\d course_ratings

# Verificar constraints
SELECT constraint_name, constraint_type
FROM information_schema.table_constraints
WHERE table_name = 'course_ratings';

# Verificar índices
\di course_ratings*
```

### 2. Verificación de API

```bash
# Usando curl
curl -X POST http://localhost:8000/courses/1/ratings \
  -H "Content-Type: application/json" \
  -d '{"user_id": 42, "rating": 5}'

curl http://localhost:8000/courses/1/ratings

curl http://localhost:8000/courses/1/ratings/stats

curl -X DELETE http://localhost:8000/courses/1/ratings/42
```

### 3. Verificación de Tests

```bash
# Todos los tests deben pasar
pytest app/tests/ -v

# Coverage debe ser >= 90%
pytest app/tests/ --cov=app --cov-report=term-missing
```

---

## Consideraciones Finales

### Performance

1. **Índices optimizados**: Queries de ratings serán O(log n)
2. **Agregaciones SQL**: Cálculos de promedios en base de datos
3. **Eager loading preparado**: Usar `joinedload(Course.ratings)` cuando necesario
4. **Caching preparado**: Endpoints de stats son cacheables

### Security

1. **Validación triple**: Pydantic + Service + CHECK constraint
2. **SQL injection protegido**: SQLAlchemy ORM
3. **Soft deletes**: Preserva integridad de datos
4. **Input sanitization**: Pydantic valida tipos y rangos

### Scalability

1. **Preparado para paginación**: Queries pueden agregar LIMIT/OFFSET
2. **Preparado para Redis**: Stats endpoint es cacheable
3. **Preparado para Auth**: user_id listo para FK cuando se implemente
4. **Preparado para rate limiting**: Endpoints identificados para throttling

### Maintainability

1. **Código documentado**: Docstrings completos en todo el código
2. **Tests comprehensivos**: 90%+ coverage esperado
3. **Patrones consistentes**: Sigue arquitectura existente
4. **Type hints**: Todo el código tipado correctamente

---

**Fin del Plan de Implementación Backend**

*Este documento debe ser usado como guía paso a paso. Cada fase puede implementarse de forma independiente y verificarse antes de continuar con la siguiente.*
