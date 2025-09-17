# Plan de Implementación Técnico: Sistema de Ratings para Platziflix

**Versión**: 1.0
**Fecha**: 2025-09-17
**Estimación**: 16 horas
**Alcance**: Backend + Frontend

## Análisis Arquitectural del Contexto Actual

### Patrones Identificados
- **Backend**: Service Layer Pattern + Repository Pattern con SQLAlchemy
- **Database**: Soft deletes con `deleted_at`, timestamping automático via `BaseModel`
- **API**: Dependency Injection con FastAPI Dependencies
- **Frontend**: Next.js 15 App Router + Server Components + TypeScript strict
- **Testing**: Piramide de testing (Vitest + React Testing Library)

### Arquitectura de Datos Actual
```
BaseModel (id, created_at, updated_at, deleted_at)
├── Course (name, description, thumbnail, slug)
├── Teacher (name, email)
├── Lesson (course_id, name, description, slug, video_url)
└── CourseTeacher (course_id, teacher_id) [Many-to-Many]
```

## Plan de Implementación por Fases

### FASE 1: Database Layer (2 horas)
**Prioridad**: Crítica - Base de todo el sistema

#### 1.1 Crear Migración Alembic
- **Archivo**: `Backend/app/alembic/versions/[timestamp]_add_course_ratings_table.py`
- **Patrón**: Seguir estructura de migración existente

```sql
CREATE TABLE course_ratings (
    id INTEGER PRIMARY KEY,
    course_id INTEGER NOT NULL REFERENCES courses(id),
    user_id INTEGER NOT NULL, -- Por ahora sin FK, preparado para auth futuro
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP NULL,
    CONSTRAINT unique_user_course_rating UNIQUE(course_id, user_id, deleted_at)
);

CREATE INDEX idx_course_ratings_course_id ON course_ratings(course_id);
CREATE INDEX idx_course_ratings_user_id ON course_ratings(user_id);
```

#### 1.2 Consideraciones Técnicas de Performance
- **Índices estratégicos**: course_id (consultas frecuentes), user_id (futuras queries)
- **Constraint UNIQUE compuesto**: Incluye `deleted_at` para permitir soft deletes
- **Validación CHECK**: Rating 1-5 a nivel de BD para integridad

### FASE 2: Backend Models & Services (4 horas)

#### 2.1 Modelo CourseRating (1h)
- **Archivo**: `Backend/app/models/course_rating.py`
- **Patrón**: Herencia de `BaseModel`, siguiendo convenciones existentes

```python
class CourseRating(BaseModel):
    __tablename__ = 'course_ratings'

    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    user_id = Column(Integer, nullable=False)  # Future-proof para auth
    rating = Column(Integer, CheckConstraint('rating >= 1 AND rating <= 5'), nullable=False)

    # Relationships
    course = relationship("Course", back_populates="ratings")
```

#### 2.2 Actualizar Modelo Course (1h)
- **Archivo**: `Backend/app/models/course.py`
- **Cambios**: Agregar relationship + propiedades calculadas

```python
class Course(BaseModel):
    # ... campos existentes ...

    # Nueva relación
    ratings = relationship("CourseRating", back_populates="course", cascade="all, delete-orphan")

    @property
    def average_rating(self) -> float:
        """Calcula rating promedio dinámicamente"""
        active_ratings = [r for r in self.ratings if r.deleted_at is None]
        if not active_ratings:
            return 0.0
        return sum(r.rating for r in active_ratings) / len(active_ratings)

    @property
    def total_ratings(self) -> int:
        """Cuenta total de ratings activos"""
        return len([r for r in self.ratings if r.deleted_at is None])
```

#### 2.3 Extender CourseService (2h)
- **Archivo**: `Backend/app/services/course_service.py`
- **Patrón**: Seguir estructura de métodos existentes

```python
class CourseService:
    # ... métodos existentes ...

    def get_course_ratings(self, course_id: int) -> List[Dict[str, Any]]:
        """Obtiene todos los ratings de un curso"""

    def add_course_rating(self, course_id: int, user_id: int, rating: int) -> Dict[str, Any]:
        """Agrega/actualiza rating de usuario para curso"""

    def update_course_rating(self, course_id: int, user_id: int, rating: int) -> Dict[str, Any]:
        """Actualiza rating existente"""

    def delete_course_rating(self, course_id: int, user_id: int) -> bool:
        """Soft delete de rating"""

    def get_user_course_rating(self, course_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene rating específico de usuario para curso"""
```

#### 2.4 Optimizaciones de Performance
- **Eager Loading**: Incluir ratings en consultas de curso cuando necesario
- **Agregaciones SQL**: Calcular promedios en base de datos para performance
- **Caching Strategy**: Preparado para Redis en queries frecuentes

### FASE 3: Backend API Endpoints (2 horas)

#### 3.1 Nuevos Endpoints en main.py
- **Patrón**: Seguir estructura de dependency injection existente

```python
@app.post("/courses/{course_id}/ratings")
def add_course_rating(
    course_id: int,
    rating_data: RatingRequest,
    course_service: CourseService = Depends(get_course_service)
) -> Dict[str, Any]:
    """Agrega rating a curso"""

@app.get("/courses/{course_id}/ratings")
def get_course_ratings(
    course_id: int,
    course_service: CourseService = Depends(get_course_service)
) -> List[Dict[str, Any]]:
    """Obtiene ratings de curso"""

@app.put("/courses/{course_id}/ratings/{user_id}")
def update_course_rating(
    course_id: int,
    user_id: int,
    rating_data: RatingRequest,
    course_service: CourseService = Depends(get_course_service)
) -> Dict[str, Any]:
    """Actualiza rating existente"""

@app.delete("/courses/{course_id}/ratings/{user_id}")
def delete_course_rating(
    course_id: int,
    user_id: int,
    course_service: CourseService = Depends(get_course_service)
) -> Dict[str, str]:
    """Elimina rating (soft delete)"""
```

#### 3.2 Pydantic Models para Validación
- **Archivo**: `Backend/app/models/requests.py` (nuevo)

```python
from pydantic import BaseModel, Field

class RatingRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)

class RatingResponse(BaseModel):
    id: int
    course_id: int
    user_id: int
    rating: int
    created_at: str
    updated_at: str
```

### FASE 4: Frontend Types & API Integration (2 horas)

#### 4.1 Actualizar Types (30min)
- **Archivo**: `Frontend/src/types/index.ts`
- **Cambios**: Agregar interfaces para ratings

```typescript
export interface Course {
  id: number;
  title: string;
  teacher: string;
  duration: number;
  thumbnail: string;
  slug: string;
  // Nuevos campos
  averageRating?: number;
  totalRatings?: number;
}

export interface CourseRating {
  id: number;
  courseId: number;
  userId: number;
  rating: number;
  createdAt: string;
  updatedAt: string;
}

export interface RatingRequest {
  userId: number;
  rating: number;
}
```

#### 4.2 API Service Layer (1h)
- **Archivo**: `Frontend/src/services/api.ts` (nuevo)
- **Patrón**: Centralizar llamadas a API

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const ratingsApi = {
  getCourseRatings: async (courseId: number): Promise<CourseRating[]> => {},
  addCourseRating: async (courseId: number, data: RatingRequest): Promise<CourseRating> => {},
  updateCourseRating: async (courseId: number, userId: number, data: RatingRequest): Promise<CourseRating> => {},
  deleteCourseRating: async (courseId: number, userId: number): Promise<void> => {}
};
```

#### 4.3 Error Handling & Types (30min)
- Manejo consistente de errores HTTP
- TypeScript strict compliance
- Validación de responses del backend

### FASE 5: Frontend Components (4 horas)

#### 5.1 Componente StarRating Reutilizable (2h)
- **Archivo**: `Frontend/src/components/StarRating/StarRating.tsx`
- **Patrón**: Componente controlado con TypeScript estricto

```typescript
interface StarRatingProps {
  rating: number;
  onRatingChange?: (rating: number) => void;
  readonly?: boolean;
  size?: 'small' | 'medium' | 'large';
  showCount?: boolean;
  totalRatings?: number;
}

export const StarRating = ({
  rating,
  onRatingChange,
  readonly = false,
  size = 'medium',
  showCount = false,
  totalRatings = 0
}: StarRatingProps) => {
  // Implementación con useState para hover effects
  // CSS Modules para estilos
  // Accesibilidad con ARIA labels
};
```

**Consideraciones de UX**:
- Hover effects para interactividad
- Estados loading durante submit
- Feedback visual inmediato
- Accesibilidad completa (keyboard navigation)

#### 5.2 Actualizar Course Component (1h)
- **Archivo**: `Frontend/src/components/Course/Course.tsx`
- **Cambios**: Integrar StarRating en card view

```typescript
export const Course = ({
  id,
  title,
  teacher,
  duration,
  thumbnail,
  averageRating,
  totalRatings
}: CourseType) => {
  return (
    <article className={styles.courseCard}>
      {/* ... contenido existente ... */}
      <div className={styles.ratingSection}>
        <StarRating
          rating={averageRating || 0}
          readonly={true}
          showCount={true}
          totalRatings={totalRatings}
          size="small"
        />
      </div>
    </article>
  );
};
```

#### 5.3 Actualizar CourseDetail Page (1h)
- **Archivo**: `Frontend/src/app/course/[slug]/page.tsx`
- **Cambios**: Agregar rating interactivo

```typescript
export default async function CoursePage({ params }: { params: { slug: string } }) {
  const course = await fetchCourseBySlug(params.slug);

  return (
    <div>
      {/* ... contenido existente ... */}
      <section className={styles.ratingsSection}>
        <h3>Califica este curso</h3>
        <StarRating
          rating={userRating || 0}
          onRatingChange={handleRatingSubmit}
          size="large"
        />
        <div className={styles.ratingsStats}>
          <StarRating
            rating={course.averageRating || 0}
            readonly={true}
            showCount={true}
            totalRatings={course.totalRatings}
          />
        </div>
      </section>
    </div>
  );
}
```

### FASE 6: Testing & Quality Assurance (2 horas)

#### 6.1 Backend Tests (1h)
- **Unit Tests**: CourseService methods
- **Integration Tests**: API endpoints
- **Database Tests**: Constraints y relationships

```python
# Backend/app/tests/test_course_ratings.py
def test_add_course_rating():
def test_rating_constraints():
def test_soft_delete_ratings():
def test_average_rating_calculation():
```

#### 6.2 Frontend Tests (1h)
- **Component Tests**: StarRating interactividad
- **Integration Tests**: Rating submission flow
- **Accessibility Tests**: Keyboard navigation

```typescript
// Frontend/src/components/StarRating/__tests__/StarRating.test.tsx
describe('StarRating Component', () => {
  test('renders correct number of stars');
  test('handles rating changes');
  test('supports keyboard navigation');
  test('displays rating count correctly');
});
```

## Consideraciones Técnicas Críticas

### Performance & Escalabilidad
1. **Database Indexing**: Índices optimizados para queries frecuentes
2. **Lazy Loading**: Ratings cargados solo cuando necesario
3. **Caching Strategy**: Redis preparado para ratings agregados
4. **Pagination**: Preparado para grandes volúmenes de ratings

### Security & Data Integrity
1. **Input Validation**: Pydantic + TypeScript + CHECK constraints
2. **SQL Injection**: SQLAlchemy ORM protege automáticamente
3. **Rate Limiting**: Preparado para throttling en endpoints críticos
4. **User Validation**: user_id validation (preparado para auth futuro)

### Mantenibilidad & Extensibilidad
1. **Clean Architecture**: Separación clara de responsabilidades
2. **SOLID Principles**: Interfaces extensibles para futuras features
3. **Type Safety**: TypeScript estricto en todo Frontend
4. **Code Reuse**: StarRating component reutilizable

## Riesgos Técnicos & Mitigación

### Riesgos Identificados
1. **Performance**: Queries de agregación pueden ser costosas
   - **Mitigación**: Índices específicos + caching + paginación

2. **Data Consistency**: Concurrent ratings updates
   - **Mitigación**: UNIQUE constraints + optimistic locking

3. **UX Complexity**: Loading states durante submissions
   - **Mitigación**: Optimistic updates + rollback en errores

4. **Future Auth Integration**: user_id actualmente sin validación
   - **Mitigación**: Campo preparado, validación agregada cuando auth implemente

## Criterios de Aceptación Técnicos

### Database Layer
- ✅ Migración ejecuta sin errores
- ✅ Constraints funcionan correctamente
- ✅ Índices optimizan performance de queries

### Backend API
- ✅ Endpoints responden con códigos HTTP correctos
- ✅ Validación Pydantic funciona correctamente
- ✅ Soft deletes mantienen integridad de datos
- ✅ Cálculos de rating promedio son precisos

### Frontend Components
- ✅ StarRating renderiza correctamente en todos los tamaños
- ✅ Interactividad funciona sin errores
- ✅ Estados de loading manejan correctamente
- ✅ Accesibilidad completa implementada

### Testing
- ✅ Cobertura de tests >= 90%
- ✅ Todos los tests unitarios e integración pasan
- ✅ No hay regresiones en funcionalidad existente

### Performance
- ✅ Queries de ratings < 100ms en datasets normales
- ✅ UI responde < 200ms en interacciones
- ✅ Bundle size incrementa < 10KB

## Secuencia de Implementación Recomendada

1. **Migración DB** → **Modelo CourseRating** → **Tests DB**
2. **Actualizar Course Model** → **CourseService Methods** → **Tests Backend**
3. **API Endpoints** → **Pydantic Models** → **Tests Integration**
4. **Frontend Types** → **API Service** → **StarRating Component**
5. **Actualizar Components** → **Integration** → **Tests Frontend**
6. **QA Testing** → **Performance Testing** → **Deploy**

## Estimación Final

| Fase | Componente | Horas |
|------|------------|-------|
| 1 | Database & Migrations | 2h |
| 2 | Backend Models & Services | 4h |
| 3 | Backend API Endpoints | 2h |
| 4 | Frontend Types & Services | 2h |
| 5 | Frontend Components | 4h |
| 6 | Testing & QA | 2h |
| **TOTAL** | **Sistema de Ratings Completo** | **16h** |

---

*Este plan sigue estrictamente los patrones arquitecturales existentes de Platziflix y está diseñado para ser implementado incrementalmente, manteniendo la estabilidad del sistema en cada fase.*