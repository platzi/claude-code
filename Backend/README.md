# 🎓 Platziflix - Plataforma de Cursos Online

## Descripción del Proyecto

Platziflix es una plataforma online de cursos simple y directa. Cada curso contiene clases con descripciones básicas. Es una implementación minimalista enfocada en la funcionalidad core de distribución de contenido educativo.

## Stack Tecnológico

### Backend
- **Python** - Lenguaje principal
- **FastAPI** - Framework web moderno
- **PostgreSQL** - Base de datos relacional
- **Docker** - Contenedores para despliegue y desarrollo local

### Frontend
- **TypeScript** - Lenguaje con tipado estático
- **CSS Modules** - Estilos modulares
- **SASS** - Preprocesador de CSS

### Mobile
- **iOS**: Swift + SwiftUI
- **Android**: Kotlin + Jetpack Compose

## Arquitectura

```
Frontend (TypeScript)     Mobile Apps (Swift/Kotlin)
        │                           │
        └─────────┬─────────────────┘
                  │
            Backend API (FastAPI)
                  │
            Database (PostgreSQL)
```

## Entidades del Sistema

### Course (Curso)
- ID único
- Nombre del curso
- Descripción
- Thumbnail (imagen)
- Slug para URLs
- Profesores asignados
- Timestamps de gestión

### Class (Clase)
- ID único
- Pertenece a un curso
- Nombre de la clase
- Descripción
- Slug para URLs
- URL del video
- Timestamps de gestión

### Teacher (Profesor)
- ID único
- Nombre completo
- Email de contacto
- Timestamps de gestión


El enfoque es mantener la simplicidad y funcionalidad core sin features adicionales complejas.