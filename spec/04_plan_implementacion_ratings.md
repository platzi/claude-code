# Plan de Implementación por Fases: Completar Sistema de Ratings (1-5 estrellas)

**Versión**: 1.0
**Fecha**: 2026-09-28
**Base**: análisis de impacto verificado (IDs B* backend, F* frontend) + `spec/03_backend_security_review.md`
**Alcance**: Backend (FastAPI) + Frontend (Next.js 15). Mobile solo como fase futura.

---

## 1. Resumen y estado actual

El backend tiene el CRUD de ratings funcionando a nivel de servicio y endpoints, y el frontend solo **muestra** el promedio en las tarjetas del catálogo. **No se puede votar desde la web.** Por eso `CLAUDE.md` se equivoca al decir "Sistema de ratings completo (Backend + Frontend)", y hay que corregirlo (Fase 4).

Bloqueantes (🔴):

| ID | Problema | Fase |
|---|---|---|
| B1 | `UNIQUE(course_id,user_id,deleted_at)` no impide duplicados activos + race check-then-insert | 1 |
| B2 | Modelo `CourseRating` no declara la unicidad → drift en autogenerate | 1 |
| B4 | `user_id` lo manda el cliente (authorization bypass) | 2 (mitigación) / 5 (auth real) |
| F1 | `CourseDetail.tsx` y `course/[slug]/page.tsx` usan campos inexistentes (`title`, `teacher`, `duration`) | 1 |
| F2 | `ratingsApi.getUserRating` llama a una ruta inexistente y no maneja el 204 | 2 |
| F3 | No existe componente para votar | 3 |

Importantes/menores: B5 (N+1), B6 (errores por string), B7 (códigos HTTP), B8 (router), B9 (seed/properties), falta CORS, F6 (tipos), F7 (ids SVG), F8 (URLs/`await params`), F9 (`Course.test.tsx` roto).

### Hallazgos adicionales detectados al preparar este plan

- **A1 (amplía F8, bloqueante)**: `src/app/course/[slug]/page.tsx` tipa `params` como objeto síncrono (`params: { slug: string }`). En Next 15 el `PageProps` generado exige `Promise`, así que `yarn build` falla por tipos aunque se arregle F1. Por eso pasa a la Fase 1. `app/classes/[class_id]/page.tsx` ya usa `await params`.
- **A2 (amplía F1)**: `generateMetadata` en `course/[slug]/page.tsx` también usa `courseData.title` (título "undefined - Curso Online"). El tipo `Class` (`src/types/index.ts`) mezcla dos formas distintas: el resumen de clase dentro del detalle (`id,name,description,slug`) y la respuesta de `GET /classes/{id}` (`id,title,description,slug,video,duration`). Hay que separarlos en dos tipos.
- **A3**: `GET /classes/{class_id}` (`main.py:121-142`) no filtra `deleted_at IS NULL`, lo que rompe el patrón de soft delete. Además renombra `name→title` y devuelve `duration: 0` fijo.
- **A4**: `tests/test_rating_db_constraints.py` usa `SessionLocal` contra la **BD de desarrollo** y hace `commit()` de cursos "Test Course" que no se limpian. Cada corrida ensucia `platziflix_db`.
- **A5**: el `Makefile` no tiene un target `test`. Se agrega en la Fase 1.
- **A6**: `Backend/app/models/class_.py` es código muerto: el modelo `Class` no se exporta en `models/__init__.py` y hace `back_populates="classes"` hacia una relación que no existe en `Course`. Se elimina en la Fase 4.
- **A7 (matiza B9)**: la FK `course_id` sin `ondelete` no tiene efecto práctico porque nunca se borra físicamente (soft delete). Basta con documentarlo; no hace falta migración.
- **A8**: `tests/test_rating_endpoints.py:207` fija el 204 de `GET .../ratings/user/{id}` y `:61` el 201 en POST. Hay que ajustar esos tests cuando cambie el contrato (Fase 2).
- **A9**: el detalle solo expone `teacher_id: [int]`, así que la UI no puede mostrar "Por {profesor}". iOS decodifica `teacher_id` como opcional (`CourseDTO.swift:20`), de modo que agregar `teachers: [{id,name}]` es un cambio aditivo y seguro.

---

## 2. Supuestos y decisiones

| # | Decisión | Supuesto adoptado (pendiente de confirmar) | Alternativa |
|---|---|---|---|
| S1 | Identidad del usuario | **SUPUESTO**: usuario de prueba. El backend expone la dependencia `get_current_user_id()` en `app/core/security.py`, que lee el header `X-User-Id`. Solo lo acepta si `settings.AUTH_MODE == "demo"`; si falta, responde 401. El frontend obtiene el id en el servidor (cookie `pfx_uid`, con fallback a la env `DEMO_USER_ID`). Rutas nuevas `/courses/{id}/ratings/me`. | Auth real (JWT + tabla `users`). Pasa de la Fase 5 a una prerrequisito de la Fase 2. |
| S2 | Transporte del voto | **SUPUESTO**: Server Action de Next (`'use server'`) que llama al backend desde el servidor. No requiere CORS y `revalidatePath` refresca el promedio. | `CORSMiddleware` + `ratingsApi` desde un client component. Ver impacto abajo. |
| S3 | Upsert | `PUT /courses/{id}/ratings/me` idempotente: **201** si crea y **200** si actualiza. | Mantener `POST` como upsert (sigue siendo ambiguo en códigos). |
| S4 | "Sin rating" | `GET /me` responde **404** con `code: "RATING_NOT_FOUND"`, en JSON. `ratingsApi` lo convierte en `null` (y distingue `COURSE_NOT_FOUND`). | 200 con body `null`. |

**Si el usuario elige la alternativa de S2 (CORS + cliente):**
- Fase 2: agregar `CORSMiddleware` en `main.py` con `allow_origins=settings.CORS_ORIGINS` (por defecto `["http://localhost:3000"]`), métodos `GET, PUT, DELETE` y header `X-User-Id`, más un test de preflight.
- Fase 3: se elimina `actions.ts`. `RatingInput` llama directo a `ratingsApi.upsertMyRating` y refresca con `router.refresh()`. El user id tiene que llegar al cliente (`NEXT_PUBLIC_DEMO_USER_ID`), lo que lo deja más expuesto y empeora B4 hasta la Fase 5.
- Las Fases 1, 4 y 5 no cambian.

**Si el usuario elige auth real ya (S1)**: la Fase 5.1 se adelanta antes de la Fase 2 (+12-16 h). El resto del plan no cambia porque todo pasa por `get_current_user_id()`.

---

## 3. Fases

Comandos base (siempre dentro del contenedor; antes, confirmar con `docker-compose ps` que `api` y `db` estén `Up`):

```bash
cd Backend && make start
make migrate
make test          # nuevo target (Fase 1): docker-compose exec api bash -c "cd /app && uv run pytest"
docker-compose exec api bash -c "cd /app && uv run alembic -c app/alembic.ini check"   # detecta drift modelo vs BD

cd Frontend && yarn install && yarn test --run && yarn lint && yarn build
```

---

### Fase 1: Integridad de datos + base en verde

**Objetivo**: que la BD garantice un solo rating activo por usuario y curso, sin race conditions ni drift. Además, que el detalle de curso renderice bien y que `yarn build`, `yarn test` y `make test` pasen. Es la base sobre la que se agrega el voto.

**Backend**
1. **Migración nueva** en `Backend/app/alembic/versions/<rev>_partial_unique_active_rating.py`, con `down_revision='0e3a8766f785'`. Se crea con `make create-migration` y se edita a mano.
   - `upgrade()`:
     1. Deduplicar los activos: soft delete de todos menos el más reciente por (course_id, user_id).
        ```sql
        UPDATE course_ratings SET deleted_at = NOW(), updated_at = NOW()
        WHERE id IN (
          SELECT id FROM (
            SELECT id, ROW_NUMBER() OVER (PARTITION BY course_id, user_id
                                          ORDER BY updated_at DESC, id DESC) AS rn
            FROM course_ratings WHERE deleted_at IS NULL) t
          WHERE rn > 1);
        ```
     2. `op.drop_constraint('uq_course_ratings_user_course_deleted', 'course_ratings', type_='unique')`.
     3. `op.create_index('uq_course_ratings_active_user_course', 'course_ratings', ['course_id','user_id'], unique=True, postgresql_where=sa.text('deleted_at IS NULL'))`.
   - `downgrade()`: borrar el índice y recrear el `UniqueConstraint` original. Hay que documentar que la deduplicación no se revierte.
2. **Modelo** `Backend/app/models/course_rating.py`: agregar `__table_args__ = (Index('uq_course_ratings_active_user_course', 'course_id', 'user_id', unique=True, postgresql_where=text('deleted_at IS NULL')),)` y actualizar el docstring (B2).
3. **Service** `Backend/app/services/course_service.py`, en `add_course_rating` (líneas 147-215): envolver el `commit()` del insert en `try/except IntegrityError`. Si falla, hacer `rollback()`, volver a leer el rating activo y actualizarlo (upsert con reintento). Opcional y recomendado: reemplazarlo por `sqlalchemy.dialects.postgresql.insert(...).on_conflict_do_update(index_elements=['course_id','user_id'], index_where=CourseRating.deleted_at.is_(None), set_={...})`, que resuelve todo en una sentencia atómica.
4. **Tests BD** `Backend/app/tests/test_rating_db_constraints.py`:
   - Quitar el `@pytest.mark.skip` (línea 68). El test debe esperar `IntegrityError` con el nombre `uq_course_ratings_active_user_course`.
   - Agregar un test que permita un nuevo activo tras un soft delete.
   - Arreglar A4: fixture sobre `engine.connect()` + `connection.begin()` + `Session(bind=connection, join_transaction_mode="create_savepoint")`, con rollback al final.
5. **Tests service** `test_course_rating_service.py`: caso en que `commit` lanza `IntegrityError` y el servicio termina actualizando.
6. **Makefile**: target `test: docker-compose exec api bash -c "cd /app && uv run pytest"`, más una entrada en `help` (A5).
7. (Opcional, 0.5 h, A9) En `get_course_by_slug`, agregar `"teachers": [{"id", "name"}]` sin quitar `teacher_id`.

**Frontend**
1. `src/types/index.ts`:
   - Separar `ClassSummary { id; name; description; slug }` (detalle) y `ClassDetail { id; title; description; slug; video; duration }` (`GET /classes/{id}`).
   - `CourseDetail` pasa a tener `classes: ClassSummary[]`, `teacher_id: number[]` y `teachers?: {id:number; name:string}[]`.
   - Actualizar `app/classes/[class_id]/page.tsx` y su test para usar `ClassDetail`.
2. `src/components/CourseDetail/CourseDetail.tsx`:
   - Reemplazar `title` por `name`.
   - Eliminar `formatDuration`/`totalDuration` y la duración por clase (no hay datos).
   - Mostrar profesores solo si llega `teachers`.
3. `src/app/course/[slug]/page.tsx`: `params: Promise<{ slug: string }>` + `const { slug } = await params` en la página y en `generateMetadata`, y `courseData.name` en el metadata (A1, A2).
4. `src/components/Course/__test__/Course.test.tsx` (F9): reescribirlo con las props reales (`id,name,description,thumbnail,average_rating,total_ratings`). Como el componente renderiza 2 imágenes (thumbnail + `StarRating` con `role="img"`), usar `getByAltText` en lugar de `getByRole("img")`.
5. Nuevo `src/components/CourseDetail/__tests__/CourseDetail.test.tsx`: renderiza `name`, el número de clases y los links `/classes/{id}`, y no aparece "undefined" ni "NaN".

**Verificación**: `make migrate`, `alembic check` sin diffs, `make test` en verde (incluido el test antes saltado), `yarn test --run`, `yarn build` y una revisión manual de `/course/<slug>`.
**Terminado cuando**: una inserción concurrente o duplicada de un rating activo es rechazada por la BD, `alembic check` está limpio, los tres comandos de test/build pasan y el detalle no muestra `undefined` ni `NaN`.
**Estimación**: 7 h (backend 4, frontend 3).

---

### Fase 2: Contrato de API + capa de servicio frontend

**Objetivo**: un contrato de ratings coherente y centrado en "mi rating" (`/me`), con excepciones de dominio, códigos HTTP correctos y el router separado. `ratingsApi.ts` y los tipos quedan alineados con ese contrato.

**Backend**
1. `Backend/app/services/exceptions.py` (nuevo): `DomainError(code, message)`, con `CourseNotFoundError`, `RatingNotFoundError` e `InvalidRatingError`. El servicio lanza estas excepciones en lugar de `ValueError` (B6).
2. En `main.py`, `app.add_exception_handler(DomainError, ...)` mapea a 404/422 con el cuerpo `{"detail": str, "code": str}`. Se elimina el `if "not found" in str(e)` (~línea 190).
3. `Backend/app/core/security.py` (nuevo): `get_current_user_id(x_user_id: int | None = Header(None)) -> int`. Responde 401 `{"detail":"Not authenticated","code":"UNAUTHENTICATED"}` si falta o si `AUTH_MODE != "demo"`. En `app/core/config.py` se agregan `AUTH_MODE: str = "demo"` y `CORS_ORIGINS` (solo se usa en la alternativa de S2).
4. `Backend/app/routers/ratings.py` (nuevo, B8): `APIRouter(prefix="/courses/{course_id}/ratings", tags=["ratings"])`. Se registra con `app.include_router`. Los endpoints de ratings salen de `main.py`, y `get_course_service` se mueve a `app/core/deps.py` para evitar un import circular.
5. Service: `upsert_course_rating(course_id, user_id, rating) -> tuple[dict, bool]`, donde el bool indica si se creó.
6. **Contrato nuevo**:

   | Método | Ruta | Request | Respuesta |
   |---|---|---|---|
   | GET | `/courses/{course_id}/ratings/stats` | – | 200 stats (sin cambios) |
   | GET | `/courses/{course_id}/ratings` | – | 200 lista (sin cambios) |
   | GET | `/courses/{course_id}/ratings/me` | header `X-User-Id` | 200 `RatingResponse` / 404 `RATING_NOT_FOUND` / 404 `COURSE_NOT_FOUND` / 401 |
   | PUT | `/courses/{course_id}/ratings/me` | `{"rating": 4}` | 201 (creado) / 200 (actualizado) `RatingResponse` / 422 / 404 / 401 |
   | DELETE | `/courses/{course_id}/ratings/me` | – | 204 / 404 `RATING_NOT_FOUND` / 401 |

   Ejemplos:
   ```http
   PUT /courses/3/ratings/me
   X-User-Id: 1
   Content-Type: application/json

   {"rating": 4}
   ```
   ```json
   HTTP/1.1 201 Created
   {"id": 57, "course_id": 3, "user_id": 1, "rating": 4,
    "created_at": "2026-09-28T10:00:00", "updated_at": "2026-09-28T10:00:00"}
   ```
   ```json
   GET /courses/3/ratings/me  ->  HTTP/1.1 404
   {"detail": "User has not rated this course", "code": "RATING_NOT_FOUND"}
   ```
   ```json
   GET /courses/3/ratings/stats  ->  200
   {"average_rating": 4.25, "total_ratings": 8,
    "rating_distribution": {"1": 0, "2": 1, "3": 0, "4": 3, "5": 4}}
   ```
   - `schemas/rating.py`: nuevo `MyRatingRequest { rating: int = Field(ge=1, le=5) }` (sin `user_id`). También migrar `class Config` a `model_config = ConfigDict(from_attributes=True)` (Pydantic 2).
   - Endpoints antiguos con `user_id` (`POST /ratings`, `GET /ratings/user/{uid}`, `PUT` y `DELETE /ratings/{uid}`): marcarlos `deprecated=True` en OpenAPI. Se eliminan en la Fase 4 porque son el vector de B4.

**Frontend**
1. `src/types/rating.ts`:
   - `RatingDistribution = Record<'1'|'2'|'3'|'4'|'5', number>` y `RatingStats.rating_distribution` (F6; las claves llegan como string).
   - `MyRatingRequest { rating }`.
   - `isRatingStats` valida la distribución si está presente.
   - `CourseDetail` (en `types/index.ts`) suma `rating_distribution`.
2. `src/lib/config.ts` (nuevo): `API_URL = process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'`, como fuente única.
3. `src/services/ratingsApi.ts` (F2):
   - `getMyRating(courseId, userId)`: `GET .../ratings/me` con `X-User-Id`. Devuelve `null` solo si `code === 'RATING_NOT_FOUND'`.
   - `upsertMyRating(courseId, userId, rating)`: `PUT .../me`.
   - `deleteMyRating(courseId, userId)`: `DELETE .../me`.
   - Eliminar `getUserRating`, `createRating` y `updateRating`.
   - `handleApiResponse` acepta 204 sin body (devuelve `undefined`).
   - `getRatingStats`: no ocultar un 404 de curso inexistente.

**Tests**
- `test_rating_endpoints.py`: nuevos tests de `/me`:
  - 401 sin header.
  - PUT 201 al crear y 200 al actualizar.
  - GET 404 con `code`.
  - DELETE 204/404.
  - 422 con rating 0/6.
  - Actualizar A8.
  - Override de `get_current_user_id` vía `app.dependency_overrides`.
- `test_course_rating_service.py`: las excepciones de dominio y la tupla `created`.
- Nuevo `src/services/__tests__/ratingsApi.test.ts`, con `fetch` mockeado: `getMyRating` distingue los dos 404, el PUT envía el header, el DELETE 204 no lanza error y hay timeout → `ApiError('TIMEOUT')`.

**Verificación**: `make test`, `/docs` muestra el router `ratings` con los endpoints viejos como deprecated, `curl -i -X PUT localhost:8000/courses/1/ratings/me -H 'X-User-Id: 1' -H 'Content-Type: application/json' -d '{"rating":5}'` (201 y luego 200) y `yarn test --run`.
**Terminado cuando**: `main.py` ya no contiene endpoints de ratings, no quedan comparaciones de strings de error, el contrato `/me` está cubierto por tests y `ratingsApi` solo usa rutas existentes.
**Estimación**: 7 h (backend 4.5, frontend 2.5).

---

### Fase 3: UI de voto

**Objetivo**: que el usuario pueda calificar, cambiar o quitar su rating desde el detalle de curso, con feedback optimista y accesible. El detalle muestra el promedio y la distribución.

**Frontend**
1. `src/lib/currentUser.ts` (nuevo, `import 'server-only'`): `getCurrentUserId()` lee la cookie `pfx_uid` (`cookies()` es async en Next 15) con fallback a `process.env.DEMO_USER_ID`.
2. `src/app/course/[slug]/actions.ts` (nuevo, `'use server'`):
   - `rateCourse(courseId: number, slug: string, rating: number): Promise<ActionResult>`: revalida con `isValidRating` (una Server Action es un endpoint público), llama a `ratingsApi.upsertMyRating`, luego `revalidatePath(`/course/${slug}`)` y `revalidatePath('/')`, y devuelve `{ ok: true, rating } | { ok: false, error }`.
   - `removeRating(courseId, slug)`: equivalente con `deleteMyRating`.
3. `src/components/RatingInput/RatingInput.tsx` (nuevo, `'use client'`):
   - Props: `{ initialRating: number | null; onRate: (r:number)=>Promise<ActionResult>; onRemove: ()=>Promise<ActionResult> }`. Se inyecta la acción para poder testearla.
   - Accesibilidad: `<fieldset>` con `<legend>` "Califica este curso" y 5 `<input type="radio" name="rating">` visualmente ocultos con `<label>` de estrella y texto "N estrellas". Así se obtienen radiogroup nativo, flechas y Tab gratis. Foco visible y `aria-live="polite"` para "Guardado"/errores.
   - Estado: `useOptimistic(initialRating)` + `useTransition`. Al elegir: `startTransition(async () => { setOptimistic(r); const res = await onRate(r); if (!res.ok) setError(...) })`, con rollback automático al terminar la transición. Deshabilitado mientras `isPending`. Hover o preview visual.
   - Botón "Quitar calificación" solo si hay rating.
   - `RatingInput.module.scss` con los tokens de `vars.scss`.
4. `src/components/RatingDistribution/RatingDistribution.tsx` (nuevo, server): 5 filas del 5 al 1 con barra proporcional (`role="img"` + `aria-label="4 estrellas: 3 votos (38%)"`) y el total.
5. `CourseDetail.tsx`: sección "Valoraciones" con `StarRating` (promedio, readonly), `RatingDistribution` y `RatingInput`. Recibe `userRating` como prop.
6. `app/course/[slug]/page.tsx`: después de obtener el curso, `getMyRating(course.id, userId)` (en paralelo con lo que se pueda) y pasar `rateCourse.bind(null, course.id, slug)` como `onRate`.

**Backend**: sin cambios obligatorios. Solo se ejecuta la alternativa de S2 si se elige.

**Tests** (Vitest + RTL)
- `RatingInput.test.tsx`:
  - Renderiza 5 radios con nombre accesible.
  - Refleja `initialRating`.
  - Un click llama a `onRate(n)`.
  - Las flechas mueven la selección.
  - Muestra el valor optimista mientras la promesa está pendiente.
  - Rollback y mensaje de error cuando `ok:false`.
  - "Quitar" llama a `onRemove`.
- `RatingDistribution.test.tsx`: porcentajes, total 0 sin división por cero y claves string.
- `actions.test.ts`: con `vi.mock('next/cache')` y `ratingsApi` mockeado, rechaza el rating 7 sin llamar a la API y llama a `revalidatePath` con el slug.
- `CourseDetail.test.tsx`: incluye la sección de valoraciones.

**Verificación**: `yarn test --run`, `yarn lint`, `yarn build`. Manual con `make start` + `yarn dev`: votar, recargar (persiste), cambiar el voto (el promedio se actualiza sin recargar manualmente), quitar el voto y navegar solo con teclado.
**Terminado cuando**: se puede crear, cambiar y quitar un rating desde `/course/<slug>`, el promedio y la distribución se refrescan, la navegación por teclado y el lector de pantalla funcionan y los tests nuevos pasan.
**Estimación**: 9 h.

---

### Fase 4: Calidad, performance y limpieza

**Objetivo**: eliminar el N+1, la deuda técnica y la documentación incorrecta.

**Backend**
1. B5, en `course_service.py`:
   - `get_all_courses` pasa a una sola query: `select(Course, func.coalesce(func.avg(CourseRating.rating), 0), func.count(CourseRating.id)).outerjoin(CourseRating, and_(CourseRating.course_id == Course.id, CourseRating.deleted_at.is_(None))).where(Course.deleted_at.is_(None)).group_by(Course.id)`.
   - `get_course_rating_stats` pasa a una query con `func.count().filter(CourseRating.rating == n)` por cada estrella.
   - El resultado es 1 query para el listado en lugar de 1 + 3N.
2. Eliminar las properties `Course.average_rating` y `Course.total_ratings` (`models/course.py:40-67`) y la referencia en el docstring de `course_service.py:344`.
3. Eliminar los endpoints deprecados con `user_id` y sus tests.
4. `db/seed.py`: crear ratings de ejemplo (varios `user_id` y cursos, sin duplicados activos) y limpiarlos en `clear_all_data()`.
5. A3: `/classes/{id}` filtra `deleted_at IS NULL`.
6. A6: borrar `models/class_.py`.
7. A7: documentar en el modelo que la FK no necesita `ondelete` (soft delete).
8. `test_main.py`: los mocks de `/courses` y del detalle incluyen `average_rating`, `total_ratings` y `rating_distribution`, más aserciones de esos campos.

**Frontend**
1. F7, `StarRating.tsx`: `const gradientId = useId()`, que se pasa a `StarIcon` (`id={gradientId}`, `fill={`url(#${gradientId})`}`). Si `StarRating` se queda como server component, basta con `useId`, que funciona en ambos. También hay que quitar la prop `readonly` (no hace nada) o documentarla. Test: dos `StarRating` renderizados no comparten id.
2. F8: `src/services/coursesApi.ts` (`getCourses`, `getCourseBySlug`, `getClassById`) con el mismo patrón de `ratingsApi` (timeout, `ApiError`). Se usa en `app/page.tsx`, `course/[slug]/page.tsx` y `classes/[class_id]/page.tsx`, y se eliminan los `http://localhost:8000` hardcodeados. Documentar `API_URL`, `DEMO_USER_ID` y `NEXT_PUBLIC_API_URL` en un `Frontend/.env.example`.

**Docs**
- `CLAUDE.md`:
  - Corregir "Sistema de ratings completo".
  - Actualizar la lista de endpoints (`/me`, router `app/routers/ratings.py`, deprecados eliminados) y la tabla de paridad.
  - Documentar `make test`, `AUTH_MODE` y el índice parcial.
  - Documentar que el frontend usa Server Actions para mutaciones.

**Tests**: `make test`, incluido un test de servicio que verifica `get_all_courses` con cursos sin ratings (avg 0, total 0). Opcional: contar queries con un `event.listen(engine, "before_cursor_execute")` en un test de BD. Además, `yarn test --run` y `yarn build`.
**Terminado cuando**: `/courses` ejecuta un número constante de queries, no quedan URLs hardcodeadas ni ids SVG duplicados, `make seed-fresh` genera ratings y `CLAUDE.md` refleja la realidad.
**Estimación**: 6 h.

---

### Fase 5 (futuro, fuera del alcance inmediato)

1. **Auth real** (cierra B4): tabla `users` (BaseModel + soft delete), login con emisión de JWT (cookie httpOnly) y `get_current_user_id()` que valida el token en lugar del header. Migración con FK `course_ratings.user_id → users.id`, que requiere crear usuarios para los `user_id` existentes o limpiarlos. `AUTH_MODE=demo` queda prohibido fuera de dev. Rate limiting en `PUT /me`. **12-16 h.**
2. **iOS ratings**: DTO/Mapper de stats, `RatingRepository` y la vista en el detalle. **8-10 h.**
3. **Android**: primero el detalle de curso (no existe), después ratings. **16-20 h.**

---

## 4. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Hay duplicados activos en la BD y `CREATE UNIQUE INDEX` falla | Paso de deduplicación en la misma migración, antes del índice (se conserva el más reciente). Antes de migrar, contar los duplicados con `SELECT course_id,user_id,count(*) FROM course_ratings WHERE deleted_at IS NULL GROUP BY 1,2 HAVING count(*)>1`. |
| La deduplicación no se revierte en `downgrade` | Documentarlo en la migración. Hacer backup (`pg_dump`) antes de `make migrate` en entornos con datos reales. |
| `CREATE INDEX` bloquea escrituras en tablas grandes | Hoy el volumen es bajo. En prod: `postgresql_concurrently=True` dentro de `op.get_context().autocommit_block()`. |
| Autogenerate intenta borrar el índice parcial | Declararlo en `__table_args__` (Fase 1) y agregar `alembic check` al checklist. |
| Tests de BD ensucian la BD de dev (A4) | Fixture transaccional con savepoint (Fase 1). A futuro, una BD de test separada. |
| `X-User-Id` sigue siendo falsificable en modo demo | Se centraliza en una sola dependencia, `AUTH_MODE` restringe su uso y la llamada ocurre server-side (el id no se expone al navegador con S2). Se cierra de verdad en la Fase 5.1. |
| Server Action expuesta como endpoint público | Validación de `rating` y `courseId` en la acción. El backend valida de nuevo (Pydantic `ge/le` + CHECK en BD). |
| Mobile se rompe por los cambios de contrato | Solo hay cambios aditivos en `/courses` y el detalle (Codable y Gson ignoran los campos extra). Mobile no usa los endpoints de ratings que se eliminan. |
| Eliminar endpoints deprecados rompe a algún consumidor | Antes de la Fase 4, `grep -rn "ratings/user\|ratings/{" Frontend Mobile` debe devolver vacío. |
| `yarn build` falla por otros errores de tipos ocultos | Ejecutar `yarn build` al principio de la Fase 1 para listar todos los errores antes de estimar. |

---

## 5. Checklist final

- [x] Migración con deduplicación + índice parcial `uq_course_ratings_active_user_course` aplicada (`1f4b377797b3`). `alembic check` sin diffs en `course_ratings`. *(Queda un drift previo en `courses.slug` y `teachers.email`: unique constraint vs unique index, fuera de alcance.)*
- [x] Test de unicidad reactivado y en verde. Tests de BD sin residuos en `platziflix_db` (fixture transaccional en `app/tests/conftest.py`).
- [x] `add/upsert` resistente a concurrencia (`IntegrityError` + rollback + update en `add_course_rating`).
- [x] `make test` existe y pasa dentro del contenedor (52 passed, 0 skipped).
- [x] Router `app/routers/ratings.py`, excepciones de dominio, `get_current_user_id()` y endpoints `/me` con 201/200/204/404/401 correctos. *(`app/services/exceptions.py`, `app/core/security.py`, `app/core/deps.py`; handler `{detail, code}` en `main.py`; verificado con curl.)*
- [x] Endpoints con `user_id` en la ruta o el body eliminados. *(También `RatingRequest`, `add_course_rating` y `update_course_rating`; ningún consumidor en Frontend/Mobile.)*
- [x] `ratingsApi.ts` usa solo rutas existentes, maneja el 204 y distingue los códigos de error. Tipos con `rating_distribution`. *(Helpers compartidos en `src/services/http.ts`; `src/lib/config.ts` como fuente única de `API_URL`.)*
- [x] `CourseDetail` sin campos inexistentes. `await params` en todas las páginas dinámicas. Tipos `ClassSummary`/`ClassDetail` separados; el detalle expone `teachers` (A9).
- [x] `RatingInput` accesible (teclado + lector de pantalla), con optimistic update y rollback. `RatingDistribution` en el detalle. *(Radiogroup nativo; mientras hay una acción en curso se ignoran cambios con `aria-busy` en vez de `disabled`, para no perder el foco del teclado.)*
- [x] Server Action valida la entrada y llama a `revalidatePath` en el detalle y el catálogo. *(`app/course/[slug]/actions.ts`; el user id se resuelve en el servidor con `src/lib/currentUser.ts`, nunca llega del cliente.)*
- [x] `/courses` sin N+1. Properties muertas y `class_.py` eliminados. El seed crea ratings. *(1 query para el listado, verificado con `before_cursor_execute` en `tests/test_course_service_db.py`; stats en 1 query con `COUNT(*) FILTER`; `/classes/{id}` filtra soft delete (A3); `make seed-fresh` crea 12 ratings.)*
- [x] `StarRating` con `useId`. Sin URLs hardcodeadas. `.env.example` documentado. *(`src/services/coursesApi.ts`; prop `readonly` eliminada.)*
- [x] `yarn test --run`, `yarn lint` y `yarn build` en verde. *(86 tests; solo quedan warnings de deprecación de Sass `@import`, previos.)*
- [x] `CLAUDE.md` corregido (ratings frontend, endpoints, paridad, `make test`). *(También `AUTH_MODE`/`X-User-Id`, índice parcial, Server Actions, `.env.example` y la capa `src/services/`.)*
- [x] Decisiones S1-S4 confirmadas por el usuario (2026-09-29): usuario demo con `X-User-Id`, Server Action, `PUT /me` 201/200 y `GET /me` 404 `RATING_NOT_FOUND`.

**Estimación total Fases 1-4: ~29 h** (Fase 5 aparte: ~36-46 h).
