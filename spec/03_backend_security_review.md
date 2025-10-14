# Revisión de Seguridad: Backend Sistema de Ratings

**Versión**: 1.0
**Fecha**: 2025-10-14
**Scope**: Backend API - Rating Endpoints
**Severidad Máxima**: High
**Estado**: Requiere Acción Inmediata

---

## Resumen Ejecutivo

Esta revisión de seguridad analiza la implementación del sistema de ratings completada en las FASES 3, 4 y 5 del plan de implementación. Se identificó **1 vulnerabilidad crítica de alta severidad** que debe ser corregida antes de cualquier despliegue a producción.

### Hallazgos Principales

| # | Vulnerabilidad | Severidad | Estado | Impacto |
|---|----------------|-----------|--------|---------|
| 1 | Authorization Bypass en Rating Operations | **HIGH** | 🔴 Abierto | Manipulación de ratings sin autenticación |

---

## Vulnerabilidad #1: Authorization Bypass - Missing Access Control

### Clasificación

- **Categoría**: `authorization_bypass` / `insecure_direct_object_reference`
- **Severidad**: **HIGH**
- **CWE**: CWE-862 (Missing Authorization)
- **OWASP**: A01:2021 – Broken Access Control
- **Confidence**: 95%

### Ubicación del Código

**Archivos Afectados**:
```
Backend/app/main.py:134-176    (POST /courses/{course_id}/ratings)
Backend/app/main.py:332-373    (PUT /courses/{course_id}/ratings/{user_id})
Backend/app/main.py:385-411    (DELETE /courses/{course_id}/ratings/{user_id})
```

### Descripción Técnica

Todos los endpoints de rating (POST, PUT, DELETE) carecen completamente de controles de autenticación y autorización. El sistema acepta el parámetro `user_id` directamente desde la petición HTTP (request body o path parameter) sin ninguna validación de que el usuario que realiza la petición tiene permiso para operar en nombre de ese `user_id`.

**Código Vulnerable**:

```python
@app.post("/courses/{course_id}/ratings")
def add_course_rating(
    course_id: int,
    rating_data: RatingRequest,  # user_id viene aquí sin validación
    course_service: CourseService = Depends(get_course_service)
) -> RatingResponse:
    result = course_service.add_course_rating(
        course_id=course_id,
        user_id=rating_data.user_id,  # ⚠️ Usuario no autenticado puede especificar cualquier user_id
        rating=rating_data.rating
    )
    return RatingResponse(**result)
```

### Escenario de Explotación

#### Ataque 1: Creación Masiva de Ratings Falsos

Un atacante puede crear ratings falsos atribuidos a usuarios arbitrarios:

```bash
# Crear 1000 ratings de 1 estrella atribuidos a diferentes usuarios
for i in {1..1000}; do
  curl -X POST http://localhost:8000/courses/1/ratings \
    -H "Content-Type: application/json" \
    -d "{\"user_id\": $i, \"rating\": 1}"
done
```

**Impacto**: Manipulación del rating promedio del curso, daño a la reputación.

#### Ataque 2: Modificación de Ratings de Otros Usuarios

Un atacante puede modificar o eliminar ratings legítimos de usuarios reales:

```bash
# Modificar el rating del usuario 999
curl -X PUT http://localhost:8000/courses/1/ratings/999 \
  -H "Content-Type: application/json" \
  -d '{"user_id": 999, "rating": 1}'

# Eliminar el rating del usuario 999
curl -X DELETE http://localhost:8000/courses/1/ratings/999
```

**Impacto**: Pérdida de integridad de datos, usuarios reales pierden sus ratings legítimos.

#### Ataque 3: Ataque Competitivo entre Cursos

Un actor malicioso puede:
1. Dar 5 estrellas masivamente a su propio curso (creando usuarios ficticios)
2. Dar 1 estrella masivamente a cursos competidores
3. Manipular las estadísticas de rating para ventaja comercial

**Impacto**: Distorsión del sistema de ratings, pérdida de confianza del usuario.

### Impacto de Negocio

| Área | Impacto | Severidad |
|------|---------|-----------|
| **Integridad de Datos** | Ratings pueden ser manipulados sin restricción | 🔴 Crítico |
| **Reputación del Sistema** | Pérdida de confianza en el sistema de ratings | 🔴 Crítico |
| **Experiencia de Usuario** | Usuarios ven ratings falsos/manipulados | 🔴 Crítico |
| **Cumplimiento** | Violación de principios de autorización básicos | 🟠 Alto |
| **Competitividad** | Sistema vulnerable a manipulación comercial | 🟠 Alto |

### Prueba de Concepto (PoC)

```bash
#!/bin/bash
# PoC: Crear rating como usuario arbitrario sin autenticación

# Paso 1: Verificar que el curso existe
curl http://localhost:8000/courses/1

# Paso 2: Crear rating como usuario 12345 (sin autenticación)
curl -X POST http://localhost:8000/courses/1/ratings \
  -H "Content-Type: application/json" \
  -d '{"user_id": 12345, "rating": 1}' \
  -v

# Resultado esperado: HTTP 201 Created
# Resultado real: Rating creado exitosamente sin verificar identidad

# Paso 3: Modificar rating de otro usuario (usuario 999)
curl -X PUT http://localhost:8000/courses/1/ratings/999 \
  -H "Content-Type: application/json" \
  -d '{"user_id": 999, "rating": 1}' \
  -v

# Resultado: Rating del usuario 999 modificado sin autorización
```

---

## Recomendaciones de Remediación

### Solución Recomendada (Prioridad 1)

#### 1. Implementar Sistema de Autenticación

**Prerequisito**: Implementar autenticación JWT o similar.

```python
# Backend/app/core/auth.py (nuevo archivo)
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Valida el token JWT y extrae el user_id autenticado.

    Returns:
        dict con {'id': user_id, 'email': email, ...}

    Raises:
        HTTPException 401 si token inválido
    """
    token = credentials.credentials
    # TODO: Validar token JWT
    # TODO: Extraer user_id del payload
    # TODO: Verificar que usuario existe y está activo

    # Por ahora, placeholder:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required"
    )
```

#### 2. Actualizar Endpoints con Autenticación/Autorización

```python
# Backend/app/main.py

from app.core.auth import get_current_user

@app.post(
    "/courses/{course_id}/ratings",
    response_model=RatingResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["ratings"]
)
def add_course_rating(
    course_id: int,
    rating_data: RatingRequest,
    current_user: dict = Depends(get_current_user),  # ✅ Autenticación requerida
    course_service: CourseService = Depends(get_course_service)
) -> RatingResponse:
    """
    Add a new rating to a course.

    Security:
    - Requires valid JWT authentication
    - User can only create ratings for themselves
    """
    # ✅ Validación de autorización: user_id debe coincidir con usuario autenticado
    if rating_data.user_id != current_user['id']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create rating for another user"
        )

    try:
        result = course_service.add_course_rating(
            course_id=course_id,
            user_id=current_user['id'],  # ✅ Usar user_id del token autenticado
            rating=rating_data.rating
        )
        return RatingResponse(**result)
    except ValueError as e:
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


@app.put(
    "/courses/{course_id}/ratings/{user_id}",
    response_model=RatingResponse,
    tags=["ratings"]
)
def update_course_rating(
    course_id: int,
    user_id: int,
    rating_data: RatingRequest,
    current_user: dict = Depends(get_current_user),  # ✅ Autenticación requerida
    course_service: CourseService = Depends(get_course_service)
) -> RatingResponse:
    """
    Update an existing course rating.

    Security:
    - Requires valid JWT authentication
    - User can only update their own ratings
    """
    # ✅ Validación de autorización: solo el propietario puede actualizar
    if user_id != current_user['id']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update another user's rating"
        )

    # ✅ Validación adicional: user_id en body debe coincidir con path
    if rating_data.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id in body must match user_id in path"
        )

    try:
        result = course_service.update_course_rating(
            course_id=course_id,
            user_id=current_user['id'],  # ✅ Usar user_id autenticado
            rating=rating_data.rating
        )
        return RatingResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@app.delete(
    "/courses/{course_id}/ratings/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["ratings"]
)
def delete_course_rating(
    course_id: int,
    user_id: int,
    current_user: dict = Depends(get_current_user),  # ✅ Autenticación requerida
    course_service: CourseService = Depends(get_course_service)
) -> None:
    """
    Delete (soft delete) a course rating.

    Security:
    - Requires valid JWT authentication
    - User can only delete their own ratings
    """
    # ✅ Validación de autorización: solo el propietario puede eliminar
    if user_id != current_user['id']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete another user's rating"
        )

    success = course_service.delete_course_rating(
        course_id,
        current_user['id']  # ✅ Usar user_id autenticado
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active rating found for user {user_id} on course {course_id}"
        )

    return None
```

#### 3. Simplificar Schema de Rating (Opcional pero Recomendado)

Eliminar `user_id` del request body ya que debe obtenerse del token:

```python
# Backend/app/schemas/rating.py

class RatingRequest(BaseModel):
    """
    Schema for creating or updating a course rating.

    Note: user_id is extracted from authentication token, not from request body.
    """
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="Rating value from 1 (worst) to 5 (best)"
    )

    @field_validator('rating')
    @classmethod
    def validate_rating_range(cls, v: int) -> int:
        """Additional validation for rating range."""
        if not 1 <= v <= 5:
            raise ValueError('Rating must be between 1 and 5')
        return v
```

Actualizar endpoints:

```python
@app.post("/courses/{course_id}/ratings")
def add_course_rating(
    course_id: int,
    rating_data: RatingRequest,  # Ya no incluye user_id
    current_user: dict = Depends(get_current_user),
    course_service: CourseService = Depends(get_course_service)
) -> RatingResponse:
    result = course_service.add_course_rating(
        course_id=course_id,
        user_id=current_user['id'],  # ✅ Siempre del token
        rating=rating_data.rating
    )
    return RatingResponse(**result)
```

### Solución Temporal (Si Auth No Está Disponible)

Si el sistema de autenticación completo no puede implementarse inmediatamente:

#### Opción A: Deshabilitar Endpoints Hasta Auth

```python
# Backend/app/main.py

@app.post("/courses/{course_id}/ratings")
def add_course_rating(*args, **kwargs):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Rating system temporarily disabled pending authentication implementation"
    )
```

#### Opción B: Rate Limiting + Logging (NO RECOMENDADO - Mitigación Parcial)

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/courses/{course_id}/ratings")
@limiter.limit("5/minute")  # Máximo 5 ratings por minuto por IP
def add_course_rating(
    request: Request,
    course_id: int,
    rating_data: RatingRequest,
    course_service: CourseService = Depends(get_course_service)
) -> RatingResponse:
    # ⚠️ ESTO NO SOLUCIONA LA VULNERABILIDAD
    # Solo reduce el impacto de abuso masivo

    # Logging para auditoría
    logger.warning(
        f"Unauthenticated rating submission: "
        f"IP={request.client.host}, course_id={course_id}, "
        f"user_id={rating_data.user_id}, rating={rating_data.rating}"
    )

    result = course_service.add_course_rating(
        course_id=course_id,
        user_id=rating_data.user_id,
        rating=rating_data.rating
    )
    return RatingResponse(**result)
```

**⚠️ IMPORTANTE**: Esta solución temporal NO previene la vulnerabilidad, solo reduce el impacto. NO debe usarse en producción.

---

## Plan de Acción

### Timeline Recomendado

| Fase | Acción | Responsable | Deadline | Estado |
|------|--------|-------------|----------|--------|
| 1 | Implementar sistema de autenticación JWT | Backend Team | Sprint Actual | 🔴 Pendiente |
| 2 | Actualizar endpoints con `get_current_user` | Backend Team | Sprint Actual | 🔴 Pendiente |
| 3 | Actualizar schemas (remover user_id del body) | Backend Team | Sprint Actual | 🔴 Pendiente |
| 4 | Actualizar tests con autenticación | QA Team | Sprint Actual | 🔴 Pendiente |
| 5 | Security testing de endpoints protegidos | Security Team | Sprint Actual | 🔴 Pendiente |
| 6 | Code review de cambios de seguridad | Tech Lead | Sprint Actual | 🔴 Pendiente |

### Criterios de Aceptación

- [ ] Todos los endpoints de rating requieren autenticación JWT válida
- [ ] Usuario solo puede crear/modificar/eliminar sus propios ratings
- [ ] Intentos de manipular ratings de otros usuarios retornan HTTP 403
- [ ] Tests automatizados validan autorización correcta
- [ ] Documentación actualizada con requisitos de autenticación
- [ ] Security review aprobado antes de merge

---

## Impacto en Frontend

### Cambios Requeridos en Frontend

El frontend también debe actualizarse para incluir el token JWT en las peticiones:

```typescript
// Frontend/src/services/api.ts

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Obtener token JWT del almacenamiento (localStorage, cookie, etc.)
const getAuthToken = (): string | null => {
  // TODO: Implementar según estrategia de auth del proyecto
  return localStorage.getItem('auth_token');
};

export const ratingsApi = {
  addCourseRating: async (courseId: number, rating: number): Promise<CourseRating> => {
    const token = getAuthToken();

    if (!token) {
      throw new Error('Authentication required');
    }

    const response = await fetch(`${API_BASE}/courses/${courseId}/ratings`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,  // ✅ Incluir token JWT
      },
      body: JSON.stringify({ rating }),  // ✅ user_id ya no es necesario
    });

    if (response.status === 401) {
      throw new Error('Authentication expired. Please log in again.');
    }

    if (response.status === 403) {
      throw new Error('You do not have permission to perform this action.');
    }

    if (!response.ok) {
      throw new Error('Failed to submit rating');
    }

    return response.json();
  },

  // Similar para updateCourseRating y deleteCourseRating
};
```

---

## Testing de Seguridad

### Test Cases Requeridos

#### 1. Test de Autenticación Requerida

```python
# Backend/app/tests/test_rating_security.py

def test_rating_requires_authentication():
    """Test que endpoints requieren autenticación"""
    response = client.post(
        "/courses/1/ratings",
        json={"rating": 5}
    )
    assert response.status_code == 401
    assert "authentication" in response.json()["detail"].lower()


def test_invalid_token_rejected():
    """Test que tokens inválidos son rechazados"""
    response = client.post(
        "/courses/1/ratings",
        json={"rating": 5},
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
```

#### 2. Test de Autorización

```python
def test_user_cannot_rate_as_another_user(authenticated_client):
    """Test que usuario no puede crear rating para otro user_id"""
    # authenticated_client tiene user_id=100

    response = authenticated_client.post(
        "/courses/1/ratings",
        json={"user_id": 999, "rating": 5}  # Intentar rating como user 999
    )

    assert response.status_code == 403
    assert "cannot" in response.json()["detail"].lower()


def test_user_cannot_modify_another_users_rating(authenticated_client):
    """Test que usuario no puede modificar rating de otro"""
    # authenticated_client tiene user_id=100

    response = authenticated_client.put(
        "/courses/1/ratings/999",  # Intentar modificar rating del user 999
        json={"user_id": 999, "rating": 1}
    )

    assert response.status_code == 403
    assert "cannot" in response.json()["detail"].lower()


def test_user_can_only_delete_own_rating(authenticated_client):
    """Test que usuario solo puede eliminar su propio rating"""
    # authenticated_client tiene user_id=100

    response = authenticated_client.delete("/courses/1/ratings/999")

    assert response.status_code == 403
```

#### 3. Test de Flujo Completo Autorizado

```python
def test_authenticated_user_can_manage_own_rating(authenticated_client):
    """Test que usuario autenticado puede gestionar sus propios ratings"""
    # authenticated_client tiene user_id=100

    # Crear rating
    response = authenticated_client.post(
        "/courses/1/ratings",
        json={"rating": 5}
    )
    assert response.status_code == 201
    rating_data = response.json()
    assert rating_data["user_id"] == 100
    assert rating_data["rating"] == 5

    # Actualizar rating
    response = authenticated_client.put(
        "/courses/1/ratings/100",
        json={"rating": 4}
    )
    assert response.status_code == 200
    assert response.json()["rating"] == 4

    # Eliminar rating
    response = authenticated_client.delete("/courses/1/ratings/100")
    assert response.status_code == 204
```

---

## Referencias y Recursos

### Documentación Técnica

- [OWASP Top 10 2021 - A01 Broken Access Control](https://owasp.org/Top10/A01_2021-Broken_Access_Control/)
- [CWE-862: Missing Authorization](https://cwe.mitre.org/data/definitions/862.html)
- [FastAPI Security - OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)

### Herramientas Recomendadas

- **Static Analysis**: `bandit` para análisis de seguridad en Python
- **Dependency Scanning**: `safety` para vulnerabilidades en dependencias
- **API Security Testing**: OWASP ZAP, Burp Suite
- **Load Testing**: Locust para simular ataques de rating bombing

---

## Anexo: Checklist de Implementación

### Checklist de Remediación

#### Backend
- [ ] Implementar módulo de autenticación JWT (`app/core/auth.py`)
- [ ] Crear dependency `get_current_user()` para FastAPI
- [ ] Actualizar endpoint POST `/courses/{course_id}/ratings` con autenticación
- [ ] Actualizar endpoint PUT `/courses/{course_id}/ratings/{user_id}` con autenticación
- [ ] Actualizar endpoint DELETE `/courses/{course_id}/ratings/{user_id}` con autenticación
- [ ] Actualizar schema `RatingRequest` (remover `user_id` del body)
- [ ] Agregar validación de autorización en todos los endpoints
- [ ] Agregar logging de intentos de acceso no autorizado

#### Testing
- [ ] Crear tests de autenticación requerida
- [ ] Crear tests de autorización (no puede modificar ratings ajenos)
- [ ] Crear tests de flujo completo con usuario autenticado
- [ ] Ejecutar penetration testing manual
- [ ] Validar que todos los tests pasan

#### Frontend
- [ ] Actualizar servicio API para incluir token JWT en headers
- [ ] Manejar errores 401 (redirigir a login)
- [ ] Manejar errores 403 (mostrar mensaje de autorización)
- [ ] Remover `user_id` de request bodies
- [ ] Actualizar tests de componentes con autenticación

#### Documentación
- [ ] Actualizar documentación de API (Swagger/OpenAPI)
- [ ] Documentar requisitos de autenticación en README
- [ ] Actualizar guías de desarrollo con best practices de seguridad
- [ ] Documentar proceso de obtención y renovación de tokens

#### Deployment
- [ ] Configurar variables de entorno para JWT secret
- [ ] Configurar token expiration time
- [ ] Configurar refresh token mechanism
- [ ] Security review aprobado
- [ ] Deploy a staging para testing
- [ ] Validación final en staging
- [ ] Deploy a producción

---

## Historial de Cambios

| Versión | Fecha | Autor | Cambios |
|---------|-------|-------|---------|
| 1.0 | 2025-10-14 | Security Review Team | Documento inicial - Hallazgo crítico de autorización |

---

**Estado del Documento**: 🔴 **ACTIVO - REQUIERE ACCIÓN INMEDIATA**

**Próxima Revisión**: Después de implementar correcciones

**Contacto**: Para preguntas sobre este documento, contactar al Security Team.
