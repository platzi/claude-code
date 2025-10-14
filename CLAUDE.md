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
- **Lesson**: Lecciones de un curso
- **Class**: Clases individuales de una lección

### Relaciones
- Course ↔ Teacher (Many-to-Many via course_teachers)
- Course → Lesson (One-to-Many)
- Lesson → Class (One-to-Many)

## API Endpoints

- `GET /` - Bienvenida
- `GET /health` - Health check + DB connectivity
- `GET /courses` - Lista todos los cursos
- `GET /courses/{slug}` - Detalle de curso por slug

## Comandos de Desarrollo

### Backend
```bash
cd Backend
make start        # Iniciar Docker Compose
make stop         # Detener containers
make migrate      # Ejecutar migraciones
make seed         # Poblar datos de prueba
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

## Funcionalidades Implementadas

- ✅ Catálogo de cursos con grid estilo Netflix
- ✅ Detalle de cursos (profesores, lecciones, clases)
- ✅ Navegación por slug SEO-friendly
- ✅ Reproductor de video integrado
- ✅ Health checks de API y DB
- ✅ Apps móviles nativas (Android + iOS)
- ✅ Testing en todos los componentes

## Patrones de Desarrollo

### Backend
- **Arquitectura**: Service Layer Pattern
- **Dependency Injection**: FastAPI Dependencies
- **Database**: Repository Pattern con SQLAlchemy

### Frontend
- **Routing**: Next.js App Router
- **Data Fetching**: Server Components + fetch
- **Styling**: CSS Modules + SCSS
- **Testing**: Component testing con Vitest

### Mobile
- **Android**: MVVM + Jetpack Compose
- **iOS**: SwiftUI + Repository + Mapper Pattern

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