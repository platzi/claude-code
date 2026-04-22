# Plan de Implementación: Sistema de Ratings — Platziflix

**Fecha**: 2026-04-11
**Basado en**: `spec/00_sistema_ratings_cursos.md` + análisis real del codebase
**Alcance**: Backend (FastAPI) + Frontend (Next.js 15)

---

## Estado actual del codebase

### Lo que YA existe y funciona

**Backend:**
- Modelo `CourseRating` completo con FK, CHECK constraint y relationship
- `CourseService` con los 6 métodos de ratings
- Todos los endpoints en `main.py` (POST, GET lista, GET stats, GET user, PUT, DELETE)
- `schemas/rating.py` con `RatingRequest`, `RatingResponse`, `RatingStatsResponse`
- Migración `0e3a8766f785` con tabla `course_ratings`, índices y FK

**Frontend:**
- `ratingsApi.ts` — cliente HTTP completo con timeout y AbortController
- `rating.ts` — tipos base (incompletos, ver Fase F1)
- `StarRating` — componente funcional pero solo en modo readonly
- `Course.tsx` — ya consume `average_rating` y `total_ratings`
- `page.tsx` (home) — ya pasa los datos de rating al componente `Course`

### Lo que falta o tiene problemas

El spec original estaba desactualizado. Las fases a continuación cubren **correcciones reales, tests faltantes e integración visual**.

---

## Backend — 5 Fases

### Fase B1 — Migración: UNIQUE constraint correcto

**Prioridad**: CRÍTICA — debe hacerse primero

**Problema**: El constraint actual `UNIQUE(course_id, user_id, deleted_at)` no funciona correctamente en PostgreSQL porque `NULL != NULL`. Dos ratings activos del mismo usuario en el mismo curso pueden coexistir bajo race condition. La protección hoy es solo lógica del service (SELECT previo), que es insuficiente bajo concurrencia.

El test `test_unique_constraint_prevents_duplicate_active_ratings` está marcado con `@pytest.mark.skip` exactamente por este motivo.

**Archivos:**
| Acción | Archivo |
|--------|---------|
| Crear | `Backend/app/alembic/versions/<hash>_add_partial_unique_index_ratings.py` |

**Qué hace la migración:**
1. Elimina el constraint `uq_course_ratings_user_course_deleted`
2. Crea un PARTIAL UNIQUE INDEX:
   ```sql
   CREATE UNIQUE INDEX uix_active_rating_per_user_course
   ON course_ratings (course_id, user_id)
   WHERE deleted_at IS NULL
   ```

**Criterio de done:**
- `make migrate` ejecuta sin errores
- El test `test_unique_constraint_prevents_duplicate_active_ratings` pasa al quitarle el `@pytest.mark.skip`
- `test_unique_constraint_allows_soft_deleted_duplicates` sigue pasando

**⚠ Antes de migrar:** verificar que no existen datos corruptos:
```sql
SELECT course_id, user_id, COUNT(*)
FROM course_ratings
WHERE deleted_at IS NULL
GROUP BY course_id, user_id
HAVING COUNT(*) > 1;
```
Si hay resultados, la migración va a fallar al crear el índice.

---

### Fase B2 — Tests de integración reales (sin mocks de DB)

**Prioridad**: Alta — el spec lo exige explícitamente

**Depende de**: B1 (para el test de race condition)

**Problema**: Los tests actuales en `test_course_rating_service.py` usan `Mock()` para la sesión de SQLAlchemy. No existen tests de integración end-to-end del service contra PostgreSQL real.

**Archivos:**
| Acción | Archivo |
|--------|---------|
| Crear | `Backend/app/tests/conftest.py` |
| Crear | `Backend/app/tests/test_course_rating_service_integration.py` |
| Modificar | `Backend/app/tests/test_rating_db_constraints.py` (activar skip) |

**Casos obligatorios en `test_course_rating_service_integration.py`:**
- `test_add_rating_creates_record` — verifica fila en DB
- `test_add_rating_upsert_updates_existing` — segundo POST mismo user actualiza, no duplica
- `test_soft_delete_sets_deleted_at` — `deleted_at` no es None después del delete
- `test_soft_delete_allows_new_rating_after_delete` — se puede crear uno nuevo post-delete
- `test_get_stats_sql_aggregation` — avg y distribución correctos contra datos reales
- `test_concurrent_race_condition_prevention` — dos upserts simultáneos no crean duplicados

**Criterio de done:**
- `pytest Backend/app/tests/test_course_rating_service_integration.py -v` pasa al 100% con Docker corriendo
- Ningún fixture de DB usa `Mock()` ni `MagicMock()`

**Riesgo**: Necesita DB de test aislada o el fixture debe hacer rollback/`TRUNCATE` al finalizar. Verificar si existe `TEST_DATABASE_URL` en `config.py` o si hay que agregarlo.

---

### Fase B3 — Fix semántico HTTP: status 204 y 201/200

**Prioridad**: Media — correctitud del contrato HTTP

**Independiente de** B2 y B4.

**Problemas:**
1. `GET .../ratings/user/{user_id}` lanza `HTTPException(status_code=204)` — un 204 no es un error HTTP, no debe ser una excepción.
2. `POST .../ratings` siempre retorna 201 aunque sea un update (upsert). El contrato del spec es 201 en create, 200 en update.

**Archivos:**
| Acción | Archivo |
|--------|---------|
| Modificar | `Backend/app/main.py` |
| Modificar | `Backend/app/tests/test_rating_endpoints.py` |

**Cambios en `main.py`:**
- `get_user_course_rating`: usar `from fastapi.responses import Response` y retornar `Response(status_code=204)` cuando el rating no existe
- `add_course_rating` (POST): el service ya diferencia create vs. update internamente; exponer esa diferencia retornando 201 en create y 200 en update

**Criterio de done:**
- `GET .../user/{user_id}` retorna verdadero 204 (no excepción)
- `POST .../ratings` retorna 201 en create y 200 en update
- Tests cubren ambos status codes del POST

**⚠ Breaking change**: cambiar el status del POST de 201 a 200 en update puede afectar clientes existentes. Documentar en el commit.

---

### Fase B4 — Proteger properties Python en Course

**Prioridad**: Media — prevención de N+1 futuros

**Independiente** de todas las demás fases.

**Problema**: `Course.average_rating` y `Course.total_ratings` como `@property` en el modelo iteran sobre `self.ratings` en Python (lazy load). El `CourseService` ya usa SQL correctamente con `get_course_rating_stats()`. El riesgo es que alguien use los properties directamente en un endpoint futuro y genere N+1 queries sin notarlo.

**Archivos:**
| Acción | Archivo |
|--------|---------|
| Modificar | `Backend/app/models/course.py` |

**Opciones (elegir una):**
- Renombrar a `_average_rating_python` y `_total_ratings_python` para marcarlos como privados
- Agregar docstring de advertencia explícito indicando que no deben usarse en respuestas API

**Criterio de done:**
- Ningún endpoint en `main.py` accede a `course.average_rating` directamente (verificar con grep)
- La opción elegida está documentada en el código

---

### Fase B5 — Verificación final

**Depende de**: todas las fases anteriores

**Acciones:**
1. `make migrate` — verificar que ambas migraciones están aplicadas
2. `pytest Backend/app/tests/ -v --tb=short` — suite completa
3. Verificar que el test de Fase B1 (quitado el skip) pasa
4. `GET /health` responde `{"status": "ok", "database": true}`

**Criterio de done:**
- 0 tests fallando
- 0 tests skipeados

---

## Frontend — 6 Fases

### Fase F1 — Corregir tipos en `rating.ts`

**Prioridad**: CRÍTICA — base de todo el frontend

**Problema**: `RatingStats` no modela `rating_distribution` (el backend ya lo devuelve). `isRatingStats()` no valida ese campo. Los tipos usan `snake_case` — decisión de convención pendiente.

**Archivos:**
| Acción | Archivo |
|--------|---------|
| Modificar | `Frontend/src/types/rating.ts` |

**Cambios:**
1. Agregar `rating_distribution: Record<1 | 2 | 3 | 4 | 5, number>` a `RatingStats`
2. Actualizar `isRatingStats()` para validar los tres campos incluyendo la distribución
3. **Decisión de naming** (tomar antes de implementar):
   - **Opción A** (recomendada): mantener `snake_case` porque los datos vienen directamente del fetch sin mapper
   - **Opción B**: crear mapper en `ratingsApi.ts` para transformar a `camelCase` al cruzar la frontera HTTP

**Criterio de done:**
- `npx tsc --noEmit` pasa sin errores
- `isRatingStats()` valida `rating_distribution`
- Sin cambios en componentes ni en `ratingsApi.ts`

**Riesgo**: Si se elige Opción B (camelCase), `ratingsApi.ts` necesita mapper y todos los consumidores existentes rompen. Definir esto aquí evita regresiones.

---

### Fase F2 — Corregir tests rotos de Course

**Prioridad**: Alta — deuda técnica bloqueante

**Independiente** de F1, puede ir en paralelo.

**Problema**: `Course.test.tsx` referencia props `title`, `teacher`, `duration` que el componente real NO tiene. Los tests están rotos pero no fallan de forma obvia porque las assertions pasan por razones incorrectas.

**Archivos:**
| Acción | Archivo |
|--------|---------|
| Modificar | `Frontend/src/components/Course/__test__/Course.test.tsx` |

**Cambios:**
1. Reemplazar `mockCourse` para usar props reales: `{ id, name, description, thumbnail, average_rating, total_ratings }`
2. Eliminar assertions sobre `teacher` y `duration`
3. Agregar casos:
   - Renderiza `StarRating` cuando `average_rating` está definido
   - NO renderiza `StarRating` cuando `average_rating` es `undefined`

**Criterio de done:**
- `yarn test` pasa 100% en `Course.test.tsx`
- Sin cambios en `Course.tsx`

---

### Fase F3 — Extender StarRating a modo interactivo

**Prioridad**: Alta — componente central del sistema

**Depende de**: F1

**Problema**: `StarRating` existe solo en modo readonly. Además, `id="halfStarGradient"` es un atributo global en el DOM — si hay dos instancias en la misma página (readonly + interactivo), los IDs colisionan y la media estrella se rompe visualmente.

**Archivos:**
| Acción | Archivo |
|--------|---------|
| Modificar | `Frontend/src/components/StarRating/StarRating.tsx` |
| Modificar | `Frontend/src/components/StarRating/StarRating.module.scss` |
| Modificar | `Frontend/src/components/StarRating/__tests__/StarRating.test.tsx` |

**Cambios en `StarRating.tsx`:**

Props nuevas:
```typescript
onRatingChange?: (rating: number) => void
isLoading?: boolean
disabled?: boolean
```

Lógica nueva:
- Estado interno `hoveredRating: number | null` con `useState` — activo solo cuando `onRatingChange` está definido
- En modo interactivo: renderizar `<button>` por estrella (no `<span>`), con `onClick`, `onMouseEnter`, `onMouseLeave`
- Rating visual: `hoveredRating ?? rating` — el hover tiene prioridad
- `isLoading === true`: deshabilitar botones, clase CSS `loading`, cursor `wait`
- `role="group"` en modo interactivo, `role="img"` en readonly
- `aria-label` del contenedor: `"Califica este curso"` en modo interactivo
- Cada `<button>`: `aria-label="Calificar {n} de 5 estrellas"` y `aria-pressed={rating === n}`
- Fix del ID del gradiente SVG: usar `useId()` de React 18 para generar ID único por instancia

**Cambios en SCSS:**
- `.interactive button`: `cursor: pointer`, `background: none`, `border: none`, `padding: 0`
- `.loading`: `opacity: 0.6`, `cursor: wait`, `pointer-events: none`
- `.interactive button:focus-visible`: outline visible para navegación por teclado

**Tests nuevos (suite `Interactive Mode`):**
- Llama `onRatingChange` con el valor correcto al hacer click
- Muestra hover visual al `mouseenter`
- Limpia hover al `mouseleave`
- Renderiza `<button>` (no `<span>`) cuando `onRatingChange` está definido
- Deshabilita botones cuando `isLoading === true`
- No llama `onRatingChange` cuando `disabled === true`
- `aria-label` correcto en cada botón
- `aria-pressed="true"` en el botón correspondiente al rating actual
- Keyboard: `Enter` en un botón dispara `onRatingChange`

**Criterio de done:**
- `yarn test` pasa en `StarRating.test.tsx` incluyendo los nuevos casos
- Modo readonly NO regresiona — tests anteriores pasan sin cambios
- En readonly: `role="img"`, sin botones
- En interactivo: `role="group"`, con 5 botones y ARIA correcto

---

### Fase F4 — Crear componente RatingSection

**Prioridad**: Alta — frontera Client/Server necesaria

**Depende de**: F3

**Por qué es necesario**: `CourseDetail` es Server Component y no puede tener estado. `RatingSection` es el Client Component que encapsula toda la lógica de estado del rating interactivo.

**Archivos:**
| Acción | Archivo |
|--------|---------|
| Crear | `Frontend/src/components/RatingSection/RatingSection.tsx` |
| Crear | `Frontend/src/components/RatingSection/RatingSection.module.scss` |
| Crear | `Frontend/src/components/RatingSection/__tests__/RatingSection.test.tsx` |

**Interfaz del componente:**
```typescript
interface RatingSectionProps {
  courseId: number
  initialStats: {
    average_rating: number
    total_ratings: number
  }
}
```

**Estado interno:**
- `userRating: number | null` — rating actual del usuario
- `ratingState: 'idle' | 'loading' | 'success' | 'error'`
- `stats: { average_rating: number; total_ratings: number }` — inicializado desde `initialStats`
- `errorMessage: string | null`

**Lógica clave:**

`useEffect` al montar: llamar `ratingsApi.getUserRating(courseId, 1)` y setear `userRating` si existe. El userId es `1` hardcodeado con comentario `// TODO: replace with auth context`.

`handleRatingChange(newRating)`:
1. Guardar `previousRating` y `previousStats`
2. **Optimistic update**: actualizar `userRating` y `stats` localmente antes del fetch
3. Setear `ratingState = 'loading'`
4. Si `previousRating === null`: `ratingsApi.createRating(...)`, si no: `ratingsApi.updateRating(...)`
5. En error: revertir a `previousRating` y `previousStats`, setear `ratingState = 'error'`
6. En éxito: `ratingState = 'success'`, refetch de `getRatingStats` para sincronizar el promedio real

Recálculo optimístico del average:
- Rating nuevo: `(avg * total + newRating) / (total + 1)`
- Actualización: `(avg * total - previousRating + newRating) / total`

**Render:**
- `StarRating` readonly con `stats` globales (promedio + total)
- `StarRating` interactivo con `userRating` del usuario
- Mensaje de error con `role="alert"` (solo en estado error)
- Mensaje de éxito con `role="status"` (solo en estado success)

**Tests requeridos (8 casos):**
1. Carga el rating del usuario al montar
2. Muestra rating previo en la estrella interactiva si existe
3. Muestra estrella vacía si no hay rating previo
4. Click aplica optimistic update ANTES de que resuelva el fetch
5. Click con éxito muestra mensaje de success
6. Click con error de red revierte al estado previo
7. `role="alert"` aparece solo en estado error
8. `role="status"` aparece solo en estado success

**Criterio de done:**
- `'use client'` en la primera línea del archivo
- Los 8 casos de test pasan
- Ninguna llamada a `ratingsApi` está en un Server Component

---

### Fase F5 — Integrar RatingSection en CourseDetail

**Depende de**: F4

**Problemas detectados:**
1. `CourseDetail.tsx` usa `course.title` y `course.teacher` pero la interfaz `CourseDetail` tiene `name` (no `title`) y no tiene `teacher`. TypeScript strict debería marcar esto.
2. El fetch de stats necesita el `courseId` que solo se conoce después de fetchear el curso — no es posible paralelizarlo sin cambiar el backend.

**Archivos:**
| Acción | Archivo |
|--------|---------|
| Modificar | `Frontend/src/app/course/[slug]/page.tsx` |
| Modificar | `Frontend/src/components/CourseDetail/CourseDetail.tsx` |
| Modificar | `Frontend/src/components/CourseDetail/CourseDetail.module.scss` |

**Cambios en `page.tsx`:**
- Fetch secuencial: primero `courseData` por slug, luego `getRatingStats(courseData.id)`
- Pasar `initialStats` como prop a `CourseDetailComponent`

**Cambios en `CourseDetail.tsx`:**
- Agregar prop `initialStats` a la interfaz
- Corregir uso de `course.title` → `course.name` y eliminar referencias a `course.teacher` si no existe en el tipo
- Renderizar `<RatingSection courseId={course.id} initialStats={initialStats} />`

**Cambios en `CourseDetail.module.scss`:**
- `.ratingSection`: separación visual (`margin-top: 1.5rem`, `padding-top: 1.5rem`, `border-top`)

**Criterio de done:**
- La página de detalle muestra `RatingSection` visualmente
- `npx tsc --noEmit` pasa sin errores (sin el bug de `title` vs `name`)
- `yarn test` sigue pasando — no se rompen tests existentes

**Riesgo**: El fetch secuencial agrega latencia al SSR. Aceptable para el scope actual. Si fuera crítico, la solución es modificar el endpoint del backend para incluir stats en el response del curso.

---

### Fase F6 — Tests de `ratingsApi.ts`

**Independiente** de F3-F5, puede ir en paralelo.

**Problema**: El servicio existe y funciona pero no tiene tests.

**Archivos:**
| Acción | Archivo |
|--------|---------|
| Crear | `Frontend/src/services/__tests__/ratingsApi.test.ts` |

**Casos requeridos:**

`getRatingStats`:
- Retorna stats correctas en 200
- Retorna `{ average_rating: 0, total_ratings: 0 }` cuando responde 404
- Lanza `ApiError` con `status: 408` cuando el fetch supera el timeout de 10s

`getUserRating`:
- Retorna `CourseRating` en 200
- Retorna `null` en 404
- Lanza `ApiError` en 500

`createRating`:
- Hace POST con el body correcto
- Retorna `CourseRating` en 201
- Lanza `ApiError` en 400 con el mensaje del backend

`updateRating`:
- Hace PUT al endpoint correcto `courses/{id}/ratings/{userId}`
- Retorna `CourseRating` en 200

`deleteRating`:
- No lanza error en 204
- Lanza `ApiError` en 404

**Criterio de done:**
- Todos los casos pasan
- 100% mockeado con `vi.spyOn(global, 'fetch')` — sin llamadas reales a la red

**⚠ Test de timeout**: usar `vi.useFakeTimers()` en el describe correspondiente y `vi.useRealTimers()` en `afterEach`. Sin esto el test del AbortController cuelga indefinidamente.

---

## Árbol de dependencias

```
Backend                                Frontend
                                       
B1 (partial unique index)              F1 (tipos) ──→ F3 (StarRating interactivo) ──→ F4 (RatingSection) ──→ F5 (integración)
 └──→ B2 (tests integración real)      
                                       F2 (fix tests Course)  ← independiente
B3 (fix 204 / 201 vs 200)             
 └── independiente                     F6 (tests ratingsApi)  ← independiente

B4 (properties Python)                 
 └── independiente

B5 (verificación final) ← al final de todo
```

**Cadenas bloqueantes:**
- Backend: B1 → B2
- Frontend: F1 → F3 → F4 → F5

**Pueden ir en paralelo:**
- B3, B4 (con cualquier fase de backend)
- F2, F6 (con cualquier fase de frontend)
- El trabajo de backend y frontend es completamente independiente entre sí

---

## Resumen de archivos por fase

| Fase | Crea | Modifica |
|------|------|----------|
| B1 | `alembic/versions/<hash>_partial_unique_index.py` | — |
| B2 | `tests/conftest.py`, `tests/test_course_rating_service_integration.py` | `tests/test_rating_db_constraints.py` |
| B3 | — | `main.py`, `tests/test_rating_endpoints.py` |
| B4 | — | `models/course.py` |
| B5 | — | ninguno (solo ejecución) |
| F1 | — | `src/types/rating.ts` |
| F2 | — | `src/components/Course/__test__/Course.test.tsx` |
| F3 | — | `StarRating.tsx`, `StarRating.module.scss`, `StarRating.test.tsx` |
| F4 | `RatingSection/RatingSection.tsx`, `RatingSection.module.scss`, `RatingSection.test.tsx` | — |
| F5 | — | `course/[slug]/page.tsx`, `CourseDetail.tsx`, `CourseDetail.module.scss` |
| F6 | `services/__tests__/ratingsApi.test.ts` | — |
