# Platziflix — Curso de Claude Code (Platzi)

> Proyecto multi-plataforma desarrollado durante el curso de Claude Code con el profesor **Eduardo Alvarez**.

## Descripcion

Platziflix es una plataforma de cursos online estilo Netflix con arquitectura multi-plataforma: API REST centralizada consumida por clientes web, iOS y Android.

## Estructura del Proyecto

```
claude-code/
├── Backend/                # API FastAPI + PostgreSQL
├── Frontend/               # Web app Next.js 15
└── Mobile/
    ├── PlatziFlixAndroid/  # App nativa Kotlin + Jetpack Compose
    └── PlatziFlixiOS/      # App nativa Swift + SwiftUI
```

## Stack Tecnologico

| Plataforma | Tecnologias |
|------------|-------------|
| **Backend** | Python 3.11, FastAPI, SQLAlchemy 2.0, PostgreSQL 15, Alembic, Docker |
| **Frontend** | Next.js 15, React 19, TypeScript 5 strict, SCSS, Vitest |
| **iOS** | Swift, SwiftUI, async/await, URLSession |
| **Android** | Kotlin, Jetpack Compose, Retrofit 2, Coroutines |

## Inicio Rapido

### Backend

```bash
cd Backend
make start        # Levanta Docker Compose (API :8000 + DB :5432)
make migrate      # Ejecuta migraciones Alembic
make seed         # Carga datos de prueba
```

### Frontend

```bash
cd Frontend
yarn install
yarn dev          # Servidor de desarrollo en :3000
```

## URLs

| Servicio | URL |
|----------|-----|
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Frontend Web | http://localhost:3000 |

## Tests

```bash
# Backend
cd Backend && make test

# Frontend
cd Frontend && yarn test
```

## Requisitos Previos

- Docker y Docker Compose
- Node.js 20+ y Yarn
- Xcode (para iOS)
- Android Studio (para Android)
