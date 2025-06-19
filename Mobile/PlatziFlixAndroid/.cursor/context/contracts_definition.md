# Platziflix

plataforma online de cursos, cada cursos tiene clases, descripciones y no hay mucho mas, eso es el inicio.

## Contratos

### Entidades
1. Curso

### Contratos

- api url: http://localhost:8000

- Course
```json
{
    "id": 1,
    "name": "Curso de React",
    "description": "Curso de React",
    "thumbnail": "https://via.placeholder.com/150", 
    "slug": "curso-de-react",
    "created_at": "2021-01-01",
    "updated_at": "2021-01-01",
    "deleted_at": "2021-01-01",
    "teacher_id": [1, 2, 3]
}
```

### Endpoints

- GET /courses -> Listar todos los cursos
```json
[
    {
        "id": 1,
        "name": "Curso de React",
        "description": "Curso de React",
        "thumbnail": "https://via.placeholder.com/150", 
        "slug": "curso-de-react",
    }
]
```
