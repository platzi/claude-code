# Platziflix — Proyecto Multi-plataforma

## Descripcion General

Platziflix es una plataforma de cursos online estilo Netflix. Arquitectura multi-plataforma con **4 proyectos independientes** que se comunican a traves de una unica API REST centralizada.

```
claude-code/
├── Backend/                # API FastAPI + PostgreSQL (fuente de verdad)
├── Frontend/               # Web app Next.js 15
└── Mobile/
    ├── PlatziFlixAndroid/  # App nativa Kotlin + Jetpack Compose
    └── PlatziFlixiOS/      # App nativa Swift + SwiftUI
```

> El Backend es la unica fuente de datos. Frontend y Mobile son clientes puros REST. No hay comunicacion directa entre clientes.

---

## Stack Tecnologico

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **ORM**: SQLAlchemy 2.0
- **DB**: PostgreSQL 15
- **Migraciones**: Alembic 1.13
- **Container**: Docker + Docker Compose
- **Gestion dependencias**: UV
- **Puerto**: 8000
- **Testing**: pytest + httpx + pytest-asyncio

### Frontend
- **Framework**: Next.js 15.3.3 con App Router + Turbopack
- **React**: 19.0 (Server + Client Components)
- **Lenguaje**: TypeScript 5 strict
- **Estilos**: SCSS 1.77 + CSS Modules
- **Testing**: Vitest 3.2.3 + React Testing Library 16.3.0 + jsdom 26.1.0
- **Gestion paquetes**: Yarn
- **Puerto**: 3000

### Mobile
- **Android**: Kotlin + Jetpack Compose + Retrofit 2 + OkHttp
- **iOS**: Swift + SwiftUI + URLSession (NetworkManager custom)

---

## Arquitectura Big Picture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENTES                                │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │  iOS (Swift) │  │Android(Kotl.)│  │   Web (Next.js 15)    │ │
│  │  SwiftUI     │  │Jetpack Comp. │  │   React 19 · TS strict│ │
│  │  :localhost  │  │  :10.0.2.2   │  │   :3000               │ │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬───────────┘ │
└─────────┼─────────────────┼──────────────────────┼─────────────┘
          │                 │    REST / JSON        │
          └─────────────────┴──────────────────────┘
                                     │
                                     ▼
          ┌──────────────────────────────────────┐
          │         FastAPI  :8000               │
          │  main.py (routing)                   │
          │  CourseService (logica de negocio)   │
          │  Depends(get_db / get_course_service)│
          └──────────────────┬───────────────────┘
                             │ SQLAlchemy 2.0 ORM
                             ▼
          ┌──────────────────────────────────────┐
          │      PostgreSQL 15  :5432            │
          │      Docker volume (persistencia)    │
          └──────────────────────────────────────┘
```

---

## Modelo de Datos (Backend)

### Entidades y relaciones

```
courses
  ├── id, name, description, thumbnail, slug (unique + index)
  ├── M2M --> teachers  (via course_teachers pivot)
  ├── 1:N --> lessons   (cascade delete)
  └── 1:N --> course_ratings (cascade delete, soft delete con deleted_at)

lessons
  ├── id, name, description, slug (indexed), video_url
  └── course_id FK --> courses (indexed)

teachers
  ├── id, name, email (unique + indexed)
  └── M2M <-> courses via course_teachers

course_ratings
  ├── id, course_id (FK indexed), user_id (indexed), rating (CHECK 1-5)
  ├── created_at, updated_at, deleted_at (soft delete)
  └── UNIQUE activo: (course_id, user_id) WHERE deleted_at IS NULL
```

### Archivos de modelos
- `Backend/app/models/base.py` — BaseModel: id, created_at, updated_at, deleted_at (abstract)
- `Backend/app/models/course.py` — Course con properties computadas `average_rating`, `total_ratings`
- `Backend/app/models/lesson.py` — Lesson con `video_url`
- `Backend/app/models/teacher.py` — Teacher con email unico
- `Backend/app/models/course_teacher.py` — Tabla pivot M2M (course_id, teacher_id)
- `Backend/app/models/course_rating.py` — Rating con soft delete y constraint de unicidad activa

### Migraciones Alembic
- `Backend/app/alembic/versions/d18a08253457_*.py` — Schema inicial (courses, teachers, lessons)
- `Backend/app/alembic/versions/0e3a8766f785_*.py` — Tabla course_ratings con soft delete

---

## API Endpoints Completos

### Sistema
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/` | Bienvenida |
| GET | `/health` | Health check + conectividad DB + conteo de cursos |

### Cursos
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/courses` | Lista todos los cursos con rating stats incluidos |
| GET | `/courses/{slug}` | Detalle de curso (teachers + lessons + rating distribution) |
| GET | `/classes/{class_id}` | Detalle de una clase/lesson por ID |

### Ratings
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | `/courses/{id}/ratings` | Crear rating — upsert, siempre retorna 201 |
| GET | `/courses/{id}/ratings` | Todos los ratings activos del curso |
| GET | `/courses/{id}/ratings/stats` | Estadisticas: promedio, total, distribucion 1-5 |
| GET | `/courses/{id}/ratings/user/{user_id}` | Rating de usuario especifico (204 si no existe) |
| PUT | `/courses/{id}/ratings/{user_id}` | Actualizar rating existente |
| DELETE | `/courses/{id}/ratings/{user_id}` | Soft delete (setea deleted_at, retorna 204) |

### Notas criticas de la API
- `POST /courses/{id}/ratings` hace **upsert**: si el usuario ya tiene rating activo lo actualiza; si no, crea uno nuevo. Siempre retorna 201.
- `DELETE` hace **soft delete** (setea `deleted_at`), preserva datos para analisis historico
- `GET /courses/{id}/ratings/user/{user_id}` retorna **204** si el usuario no ha calificado
- No hay autenticacion implementada — `user_id` se pasa como entero en el request body

---

## Estructura Backend

```
Backend/
├── app/
│   ├── main.py                  # Entry point: todos los endpoints + router
│   ├── core/config.py           # Settings via pydantic-settings (DATABASE_URL, etc.)
│   ├── db/
│   │   ├── base.py              # Engine SQLAlchemy + SessionLocal + get_db dependency
│   │   └── seed.py              # Datos de prueba (cursos, teachers, lessons, ratings)
│   ├── models/                  # ORM Models SQLAlchemy (ver lista arriba)
│   ├── schemas/
│   │   └── rating.py            # Pydantic schemas: RatingRequest, RatingResponse,
│   │                            # RatingStatsResponse, ErrorResponse
│   ├── services/
│   │   └── course_service.py    # Toda la logica de negocio (cursos + ratings)
│   │                            # Metodos: get_all_courses, get_course_by_slug,
│   │                            # get_course_rating_stats, add_course_rating (upsert),
│   │                            # update_course_rating, delete_course_rating
│   ├── alembic/                 # Configuracion y versiones de migraciones
│   │   ├── env.py
│   │   └── versions/
│   ├── tests/                   # Tests especificos de ratings
│   │   ├── test_rating_endpoints.py      # POST, GET, PUT, DELETE endpoints
│   │   ├── test_course_rating_service.py # Logica del service layer
│   │   └── test_rating_db_constraints.py # Constraints de DB (unicidad, check 1-5)
│   └── test_main.py             # Tests generales (health, cursos)
├── Dockerfile
├── docker-compose.yml           # Servicios: api (:8000) + db (:5432)
├── pyproject.toml               # Dependencias UV
└── Makefile                     # Comandos de desarrollo
```

**Patron clave**: `main.py` solo define rutas → delega toda la logica a `CourseService` via `Depends(get_course_service)`.

---

## Estructura Frontend

```
Frontend/src/
├── app/                          # Next.js App Router (Server Components por defecto)
│   ├── layout.tsx                # Root layout
│   ├── page.tsx                  # Home: grid de cursos (fetch /courses con cache: no-store)
│   ├── course/[slug]/
│   │   ├── page.tsx              # Detalle del curso con lecciones (SSR)
│   │   ├── error.tsx             # Error boundary
│   │   ├── loading.tsx           # Loading state
│   │   └── not-found.tsx         # 404 del curso
│   └── classes/[class_id]/
│       ├── page.tsx              # Reproductor de clase (SSR)
│       └── page.test.tsx         # Tests del reproductor
├── components/
│   ├── Course/
│   │   ├── Course.tsx            # Card de curso: thumbnail, nombre, StarRating integrado
│   │   └── __test__/Course.test.tsx
│   ├── CourseDetail/
│   │   └── CourseDetail.tsx      # Vista detalle: info + teachers + lista de clases
│   ├── StarRating/
│   │   ├── StarRating.tsx        # Display estrellas SVG (full/half/empty) — SOLO LECTURA
│   │   └── __tests__/StarRating.test.tsx
│   └── VideoPlayer/
│       ├── VideoPlayer.tsx       # HTML5 video element con controls
│       └── VideoPlayer.test.tsx
├── services/
│   └── ratingsApi.ts             # HTTP client tipado para ratings
│                                 # fetchWithTimeout (10s, AbortController)
│                                 # Funciones: getRatingStats, getCourseRatings,
│                                 # getUserRating, createRating, updateRating, deleteRating
├── types/
│   ├── index.ts                  # Course, Class, CourseDetail, Progress, Quiz, FavoriteToggle
│   └── rating.ts                 # CourseRating, RatingRequest, RatingStats, ApiError
│                                 # Type guards: isValidRating(), isCourseRating(), isRatingStats()
└── styles/
    ├── reset.scss
    └── vars.scss
```

**URL base API**: `process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'`

**Routing**:
- `/` → Lista de cursos
- `/course/[slug]` → Detalle del curso
- `/classes/[class_id]` → Reproductor de clase

**Notas importantes Frontend**:
- `StarRating` es componente dahoae solo lectura (display). La submission interactiva de ratings aun no esta implementada en el UI.
- `ratingsApi.ts` tiene toda la infraestructura HTTP lista para operaciones CRUD de ratings.
- `rating.ts` incluye type guards para validacion segura en runtime.

---

## Estructura Mobile

### Patron compartido (Clean Architecture / MVVM)

```
┌─────────────────────────────────────────┐
│          Presentation Layer             │
│  View (SwiftUI / Jetpack Compose)       │
│  ViewModel (estado observable)          │
└────────────────┬────────────────────────┘
                 │ inyeccion de dependencia
┌────────────────▼────────────────────────┐
│            Domain Layer                 │
│  Models: Course, Teacher, Class         │
│  Repository Protocol / Interface        │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│             Data Layer                  │
│  DTOs (deserializacion JSON)            │
│  Mappers (DTO → Domain model)           │
│  RemoteCourseRepository                 │
│  NetworkManager / Retrofit              │
└─────────────────────────────────────────┘
```

### iOS (PlatziFlixiOS)
```
PlatziFlixiOS/
├── Domain/
│   ├── Models/          # Course.swift, Teacher.swift, Class.swift
│   └── Repositories/    # CourseRepositoryProtocol.swift (async throws)
├── Data/
│   ├── Entities/        # CourseDTO.swift, TeacherDTO.swift, ClassDetailDTO.swift
│   ├── Mapper/          # CourseMapper.swift, TeacherMapper.swift, ClassMapper.swift
│   └── Repositories/    # RemoteCourseRepository.swift, CourseAPIEndpoints.swift (enum)
├── Presentation/
│   ├── Views/           # CourseListView.swift (searchable + refreshable),
│   │                    # CourseCardView.swift, DesignSystem.swift (colores/tipografia)
│   └── ViewModels/      # CourseListViewModel.swift (@MainActor, @Published, Combine)
└── Services/            # NetworkManager.swift (Singleton, generics, async/await)
                         # NetworkService.swift (protocol), APIEndpoint.swift (protocol)
                         # HTTPMethod.swift (enum), NetworkError.swift (enum)
```
- Base URL: `http://localhost:8000`
- Endpoints consumidos: `GET /courses`, `GET /courses/{slug}`
- Estado: `@Published` properties + Combine subscriptions
- Async: `async/await` nativo Swift

### Android (PlatziFlixAndroid)
```
platziflixandroid/
├── domain/
│   ├── models/          # Course.kt (data class)
│   └── repositories/    # CourseRepository.kt (interface, suspend fun, Result<T>)
├── data/
│   ├── network/         # ApiService.kt (Retrofit @GET), NetworkModule.kt (OkHttpClient)
│   ├── entities/        # CourseDTO.kt
│   ├── mappers/         # CourseMapper.kt (DTO → Domain)
│   └── repositories/    # RemoteCourseRepository.kt, MockCourseRepository.kt
├── presentation/courses/
│   ├── screen/          # CourseListScreen.kt (Scaffold + TopAppBar + LazyColumn)
│   ├── viewmodel/       # CourseListViewModel.kt (StateFlow<CourseListUiState>)
│   ├── components/      # CourseCard.kt, LoadingIndicator.kt, ErrorMessage.kt
│   └── state/           # CourseListUiState.kt (data class: isLoading, isRefreshing,
│                        #   courses, error)
│                        # CourseListUiEvent.kt (sealed: LoadCourses, RefreshCourses,
│                        #   ClearError)
├── ui/theme/            # Theme.kt, Color.kt, Type.kt, Spacing.kt (Material 3)
├── di/AppModule.kt      # DI manual con USE_MOCK_DATA flag (lazy singletons)
└── MainActivity.kt
```
- Base URL: `http://10.0.2.2:8000/` (emulador Android → localhost del host)
- Endpoints consumidos: `GET /courses`
- Estado: MVI con `StateFlow` + `CourseListUiEvent` sealed class
- `USE_MOCK_DATA` flag en `AppModule.kt` para alternar entre MockRepository y RemoteRepository

---

## Comparativa Mobile iOS vs Android

| Aspecto | iOS | Android |
|---------|-----|---------|
| UI | SwiftUI | Jetpack Compose |
| Estado | `@Published` + Combine | `StateFlow` + MVI Events |
| HTTP | URLSession custom | Retrofit 2 + OkHttp |
| Async | `async/await` nativo | `suspend` (coroutines) |
| DI | Inyeccion manual | `AppModule` con lazy + flag mock |
| Navegacion | NavigationView | Sin navegacion implementada aun |

---

## Cobertura de Funcionalidades por Plataforma

| Feature | Backend | Frontend | iOS | Android |
|---------|---------|----------|-----|---------|
| Catalogo de cursos | OK | OK | OK | OK |
| Detalle de curso | OK | OK | OK | — |
| Reproductor de video | OK | OK | — | — |
| Sistema de ratings (lectura) | OK | OK | — | — |
| Sistema de ratings (escritura) | OK | — (pendiente UI) | — | — |
| Autenticacion / usuarios | — | — | — | — |
| Health check endpoint | OK | — | — | — |

---

## Base de Datos — Conexion

| Parametro | Valor |
|-----------|-------|
| Usuario | platziflix_user |
| Password | platziflix_password |
| Database | platziflix_db |
| Host (host) | localhost |
| Host (contenedor API) | db |
| Puerto | 5432 |
| DATABASE_URL | `postgresql://platziflix_user:platziflix_password@db:5432/platziflix_db` |

---

## Comandos de Desarrollo

### Backend (siempre via Makefile, dentro del contexto Docker)

```bash
cd Backend
make start            # Levanta Docker Compose (api + db)
make stop             # Detiene los containers
make logs             # Ver logs en tiempo real
make migrate          # Ejecutar migraciones Alembic pendientes
make create-migration # Crear nueva migracion
make seed             # Poblar datos de prueba
make seed-fresh       # Reset completo + seed
```

> IMPORTANTE: Antes de ejecutar cualquier comando del Backend, verificar que el contenedor este corriendo con `docker ps`. Revisar el Makefile para ver todos los comandos disponibles.

### Frontend

```bash
cd Frontend
yarn dev              # Servidor de desarrollo :3000 (con Turbopack)
yarn build            # Build de produccion
yarn start            # Servidor de produccion
yarn test             # Ejecutar tests con Vitest
yarn lint             # ESLint
```

---

## URLs del Sistema

- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Frontend Web**: http://localhost:3000

---

## Convenciones de Codigo

| Proyecto | Naming |
|----------|--------|
| Python (Backend) | snake_case para funciones/variables, PascalCase para clases |
| TypeScript (Frontend) | camelCase para funciones/variables, PascalCase para componentes/tipos |
| Swift (iOS) | camelCase para funciones/variables, PascalCase para tipos |
| Kotlin (Android) | camelCase para funciones/variables, PascalCase para clases |

---

## Patrones Arquitectonicos por Proyecto

### Backend
- **Service Layer**: `main.py` solo define rutas, `CourseService` tiene toda la logica de negocio
- **Dependency Injection**: `Depends(get_db)` y `Depends(get_course_service)` en FastAPI
- **Soft Delete**: `course_ratings` usa `deleted_at` en lugar de borrado fisico
- **Agregacion en DB**: stats de ratings se calculan en SQL (no en Python) para eficiencia

### Frontend
- **App Router**: Server Components por defecto, Client Components solo cuando necesario
- **Data Fetching**: `fetch` con `cache: 'no-store'` en Server Components para datos frescos (SSR)
- **Servicio HTTP tipado**: `ratingsApi.ts` encapsula todos los calls con manejo de errores y timeout
- **Type Guards**: `rating.ts` expone `isValidRating()`, `isCourseRating()`, `isRatingStats()` para validacion en runtime

### Mobile (ambas plataformas)
- **Repository Pattern**: Interface/Protocol en Domain, implementacion en Data
- **DTO → Domain Mapper**: Capa separada entre modelo de red y modelo de dominio
- **ViewModel**: Expone estado observable a la View, orquesta el Repository
- **Mock Repository**: Android tiene `MockCourseRepository` + flag `USE_MOCK_DATA` para desarrollo sin backend

---

## Reglas del Proyecto

1. Docker es obligatorio para el Backend (DB + API corren en contenedores)
2. TypeScript strict activado en Frontend — no usar `any`
3. Tests requeridos para nuevas funcionalidades
4. Nuevos campos en DB siempre requieren migracion Alembic
5. La API REST es la unica fuente de datos — no hay logica de negocio en clientes
6. Los comandos del Backend deben ejecutarse verificando primero que el contenedor este activo
7. Soft delete obligatorio en entidades con historial (ratings) — nunca borrado fisico
8. Agregar estadisticas/calculos en el Service Layer del Backend, nunca en el cliente
