# Platziflix - Proyecto Multi-plataforma

## Arquitectura del Sistema

Platziflix es una plataforma de cursos online con arquitectura multi-plataforma que incluye:
- **Backend**: API REST con FastAPI + PostgreSQL
- **Frontend**: Aplicación web con Next.js 15
- **Mobile**: Apps nativas Android (Kotlin) + iOS (Swift)

## Stack Tecnológico

### Backend (FastAPI/Python)
- **Framework**: FastAPI
- **Base de datos**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0
- **Migraciones**: Alembic
- **Container**: Docker + Docker Compose
- **Gestión dependencias**: UV
- **Puerto**: 8000

### Frontend (Next.js)
- **Framework**: Next.js 15 (App Router)
- **React**: 19.0
- **Lenguaje**: TypeScript
- **Estilos**: SCSS + CSS Modules
- **Testing**: Vitest + React Testing Library
- **Fonts**: Geist Sans & Geist Mono

### Mobile
- **Android**: Kotlin + Jetpack Compose + Retrofit
- **iOS**: Swift + SwiftUI + Repository Pattern

## Estructura del Proyecto

```
claude-code/
├── Backend/           # API FastAPI + PostgreSQL
├── Frontend/          # Next.js 15 App
└── Mobile/
    ├── PlatziFlixAndroid/  # Kotlin App
    └── PlatziFlixiOS/      # Swift App
```

## Modelo de Datos

### Entidades Principales
- **Course**: Cursos (name, description, thumbnail, slug)
- **Teacher**: Profesores
- **Lesson**: Lecciones de un curso (expuesta en la API como "Class")
- **CourseRating**: Rating de un usuario a un curso (1-5), 1 rating activo por user+course

### Relaciones
- Course ↔ Teacher (Many-to-Many via course_teachers)
- Course → Lesson (One-to-Many, cascade delete-orphan)
- Course → CourseRating (One-to-Many, cascade delete-orphan)

### Patrón Soft Delete
Todas las entidades heredan de `BaseModel` (`Backend/app/models/base.py`): `id`, `created_at`, `updated_at`, `deleted_at`. **Nunca se borra físicamente** — todo query filtra por `deleted_at IS NULL`. Al agregar una entidad nueva, seguir este patrón.

## API Endpoints

- `GET /` - Bienvenida
- `GET /health` - Health check + DB connectivity (verifica conexión y cuenta `courses`)
- `GET /courses` - Lista cursos (incluye `average_rating`, `total_ratings`)
- `GET /courses/{slug}` - Detalle de curso (teachers, classes, rating stats)
- `GET /classes/{class_id}` - Detalle de una lección/clase (video, descripción)
- `GET /courses/{course_id}/ratings` - Lista ratings activos de un curso
- `GET /courses/{course_id}/ratings/stats` - Promedio + distribución 1-5 (claves `"1"`..`"5"` en el JSON)
- `GET /courses/{course_id}/ratings/me` - Rating del usuario actual: 200 / 404 `RATING_NOT_FOUND` / 404 `COURSE_NOT_FOUND` / 401
- `PUT /courses/{course_id}/ratings/me` - Upsert `{"rating": 1-5}`: **201** si crea, **200** si actualiza / 422 / 404 / 401
- `DELETE /courses/{course_id}/ratings/me` - Soft delete del rating: 204 / 404 `RATING_NOT_FOUND` / 401

**Usuario actual**: los endpoints `/me` resuelven el usuario con `get_current_user_id()` (`Backend/app/core/security.py`), que en modo demo (`AUTH_MODE=demo`, default) lee el header `X-User-Id`. **No es autenticación real**: cualquiera puede mandar cualquier id; está pensado para desarrollo hasta tener JWT (Fase 5 de `spec/04_plan_implementacion_ratings.md`). Ningún endpoint recibe `user_id` en la ruta o el body.

**Errores de negocio**: el servicio lanza excepciones de dominio (`Backend/app/services/exceptions.py`: `CourseNotFoundError`, `RatingNotFoundError`, `InvalidRatingError`, `NotAuthenticatedError`) y un handler en `main.py` las convierte en `{"detail": str, "code": str}` con 404/422/401. No comparar strings de error.

**Organización**: los endpoints de ratings viven en `Backend/app/routers/ratings.py` (`APIRouter`); cursos, clases y health siguen en `Backend/app/main.py`. La lógica de negocio está en `Backend/app/services/course_service.py` (Service Layer), inyectado vía `Depends(get_course_service)` desde `Backend/app/core/deps.py`.

## Comandos de Desarrollo

### Backend
```bash
cd Backend
make start        # Iniciar Docker Compose
make stop         # Detener containers
make migrate      # Ejecutar migraciones
make seed         # Poblar datos de prueba (cursos, lecciones y ratings)
make test         # Tests dentro del contenedor (opcional: make test ARGS="-k rating -x")
make logs         # Ver logs
```

### Frontend
```bash
cd Frontend
yarn dev          # Servidor de desarrollo
yarn build        # Build de producción
yarn test         # Ejecutar tests
yarn lint         # Linter
```

## URLs del Sistema

- **Backend API**: http://localhost:8000
- **Frontend Web**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs (FastAPI Swagger)

## Base de Datos

### Configuración Docker
- **Usuario**: platziflix_user
- **Password**: platziflix_password
- **Database**: platziflix_db
- **Puerto**: 5432

### Migraciones
- Ubicación: `Backend/app/alembic/versions/`
- Comando crear: `make create-migration`
- Comando aplicar: `make migrate`
- Detectar drift modelo vs BD: `docker-compose exec api bash -c "cd /app && uv run alembic -c app/alembic.ini check"` (hay un drift previo conocido en `courses.slug` y `teachers.email`: unique constraint vs unique index)

### Unicidad de ratings
Un solo rating **activo** por (course_id, user_id), garantizado por el índice único parcial `uq_course_ratings_active_user_course ... WHERE deleted_at IS NULL` (migración `1f4b377797b3`, declarado también en `__table_args__` del modelo). `upsert_course_rating` captura el `IntegrityError` de una carrera y actualiza el rating ganador.

### Tests de BD
Los tests que tocan la BD real usan la fixture `db_session` (`Backend/app/tests/conftest.py`): transacción externa + savepoints con rollback al final, así no dejan datos en `platziflix_db`.

## Funcionalidades Implementadas

- ✅ Catálogo de cursos con grid estilo Netflix
- ✅ Detalle de cursos (profesores, lecciones, clases)
- ✅ Navegación por slug SEO-friendly
- ✅ Reproductor de video integrado
- ✅ Health checks de API y DB
- ✅ Ratings en Backend + Frontend web: ver promedio y distribución, votar, cambiar y quitar el voto desde `/course/{slug}` (usuario demo, sin auth real todavía; ver paridad abajo)
- ✅ Apps móviles nativas (Android + iOS)
- ✅ Testing en todos los componentes

## Paridad de Features por Plataforma

**Importante al planear cualquier feature: verificar en esta tabla qué plataformas ya la tienen antes de asumir paridad.**

| Feature | Backend | Frontend Web | Android | iOS |
|---|---|---|---|---|
| Listado de cursos | ✅ | ✅ | ✅ | ✅ |
| Detalle de curso (por slug) | ✅ | ✅ | ❌ | ✅ |
| Clases/lecciones | ✅ | ✅ | ❌ | parcial (modelo existe, sin repo) |
| Ratings: ver promedio | ✅ | ✅ (catálogo + detalle con distribución) | ❌ | ❌ |
| Ratings: votar/cambiar/quitar (`/me`) | ✅ | ✅ (Server Actions) | ❌ | ❌ |

- **Android** es el cliente más atrasado: solo consume `GET /courses` (`ApiService.kt`), sin detalle de curso ni ratings.
- **iOS** tiene más cobertura que Android: `RemoteCourseRepository` implementa `getAllCourses()` y `getCourseBySlug()`, con DTOs/Mappers para Course, Class y Teacher — pero tampoco tiene ratings.
- Si se pide "agregar X en mobile", preguntar o verificar primero si aplica a Android, iOS o ambos, ya que no están a la par entre sí.

## Patrones de Desarrollo

### Backend
- **Arquitectura**: Service Layer Pattern — endpoints delgados (`main.py`, `routers/`), lógica en `CourseService`
- **Dependency Injection**: FastAPI Dependencies (`Depends(get_course_service)`, `Depends(get_current_user_id)`)
- **Database**: SQLAlchemy ORM directo (no Repository Pattern separado del Service)
- **Soft delete** en todas las entidades vía `deleted_at` (ver Modelo de Datos)
- **Agregaciones en SQL**: `GET /courses` calcula promedio y total en 1 query (LEFT JOIN + GROUP BY); no agregar properties de rating al modelo ni loops por curso (N+1)
- **Routers**: ratings ya usa `APIRouter`; al crecer cursos/clases, migrarlos igual a `app/routers/`

### Frontend
- **Routing**: Next.js App Router
- **Data Fetching**: siempre vía capa de servicio en `src/services/` (`coursesApi.ts`, `ratingsApi.ts`), sobre los helpers de `src/services/http.ts` (timeout/abort y errores tipados `ApiError` con el `code` del backend). No hay `fetch` directo ni URLs hardcodeadas en páginas/componentes; la URL sale de `src/lib/config.ts`.
- **Mutaciones**: Server Actions (`'use server'`), p. ej. `src/app/course/[slug]/actions.ts` (`rateCourse`, `removeRating`): validan la entrada (son endpoints públicos), llaman al backend desde el servidor y hacen `revalidatePath` del detalle y del catálogo. No se usa CORS: el navegador nunca llama al backend directamente.
- **Usuario actual**: `getCurrentUserId()` en `src/lib/currentUser.ts` (`server-only`): cookie `pfx_uid` con fallback a la env `DEMO_USER_ID`. Nunca se recibe el user id desde el cliente.
- **Params dinámicos**: en Next 15 `params` es `Promise` → `const { slug } = await params` (páginas y `generateMetadata`).
- **Tipos**: `ClassSummary` (clase dentro del detalle de curso) vs `ClassDetail` (`GET /classes/{id}`); `RatingDistribution` usa claves string `"1"`..`"5"`.
- **Variables de entorno**: ver `Frontend/.env.example` (`API_URL`, `NEXT_PUBLIC_API_URL`, `DEMO_USER_ID`); copiar a `.env.local`.
- **Styling**: CSS Modules + SCSS; tokens de color en `src/styles/vars.scss` (`color('...')`)
- **Testing**: Vitest + React Testing Library + `@testing-library/user-event`; en tests las clases de CSS Modules no llevan hash (`vitest.config.ts`), así que se puede usar `toHaveClass('large')`

### Mobile
- **Android**: MVVM + Jetpack Compose, Retrofit, con repo mock (`MockCourseRepository`) e inyección de dependencias (`AppModule`) — buena base pero funcionalmente incompleto (ver tabla de paridad)
- **iOS**: SwiftUI + Repository + Mapper Pattern (DTO → Domain), sin ratings todavía

## Consideraciones de Desarrollo

1. **Docker obligatorio** para el backend (DB + API)
2. **TypeScript strict** en Frontend
3. **Testing requerido** para nuevas funcionalidades
4. **Migraciones automáticas** para cambios de DB
5. **Convenciones de naming**: snake_case (Python), camelCase (JS/TS), PascalCase (Swift/Kotlin)
6. **API REST** como única fuente de datos para Frontend/Mobile

## Comandos Útiles

```bash
# Desarrollo completo
cd Backend && make start    # Iniciar backend
cd Frontend && yarn dev     # Iniciar frontend

# Reset completo de datos
cd Backend && make seed-fresh

# Ver logs de todos los servicios
cd Backend && make logs
```

Esta memoria contiene toda la información necesaria para continuar el desarrollo del proyecto Platziflix.
- Cualquier comando que necesites ejecutar para el Backend debe ser dentro del contenedor de docker API, antes de ejecutarlo certifica que esté funcionando el contenedor y revisa el archivo makefile con los comandos que existen y úsalos