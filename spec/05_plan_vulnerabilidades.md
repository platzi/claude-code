# Plan de Remediación de Seguridad: Identidad y Exposición del Sistema de Ratings

**Versión**: 1.0
**Fecha**: 2026-09-29
**Base**: revisión de seguridad de los cambios de `spec/04_plan_implementacion_ratings.md` (Fases 1-4) + `spec/03_backend_security_review.md`
**Alcance**: Backend (FastAPI) + Frontend (Next.js 15) + despliegue (Docker Compose). Mobile no consume endpoints de ratings.

---

## 1. Resumen y estado actual

La revisión de seguridad de las Fases 1-4 **no encontró vulnerabilidades nuevas** de severidad alta o media (confianza ≥ 8/10). Los cambios redujeron la superficie de ataque:

| Área | Resultado de la revisión |
|---|---|
| Identidad (`core/security.py`, `routers/ratings.py`) | Se eliminaron los endpoints con `user_id` en ruta/body (B4). Los `/me` toman el usuario solo de `get_current_user_id()`: `X-User-Id` entero positivo, 401 si `AUTH_MODE != "demo"`. |
| SQL injection | Todo es ORM con parámetros enlazados; la migración `1f4b377797b3` solo usa SQL estático. |
| Soft delete | `/classes/{id}` ya no expone lecciones borradas ni de cursos borrados. |
| Errores | El handler de `DomainError` solo devuelve `{detail, code}`; los no mapeados van al 500 por defecto sin stack trace. |
| Server Actions (`app/course/[slug]/actions.ts`) | `courseId`, `rating` y `slug` validados; user id resuelto en servidor (`lib/currentUser.ts`, `server-only`). |
| Fetch en servidor (`coursesApi.ts`, `ratingsApi.ts`) | `slug` y `class_id` pasan por `encodeURIComponent`; el host viene de env. |
| XSS | Sin `dangerouslySetInnerHTML`; todo se renderiza con JSX. |
| Secretos | `.env.example` solo contiene URLs locales y `DEMO_USER_ID=1`. |

Lo que queda son **riesgos aceptados a propósito** (decisión S1 del plan 04) y **refuerzos de despliegue**. Este plan los cierra en orden, del más barato y urgente al más grande.

### Riesgos identificados

| ID | Riesgo | Severidad si se despliega fuera de local | Fase |
|---|---|---|---|
| V1 | `auth_mode` vale `"demo"` por defecto: si alguien despliega sin definir `AUTH_MODE`, los `/me` aceptan cualquier `X-User-Id`. | Alta | 1 |
| V2 | Con `DEMO_USER_ID` definido, todos los visitantes anónimos del frontend comparten ese usuario y pueden cambiar o borrar sus votos. | Alta | 1 |
| V3 | El modo demo no autentica: cualquiera puede mandar `X-User-Id` directo al backend o fijar la cookie `pfx_uid` y actuar como otro usuario (sucesor de B4). | Alta | 3 |
| V4 | `GET /courses/{course_id}/ratings` es público y devuelve `user_id` de cada voto (preexistente): permite enumerar qué usuario votó qué. | Media (PII cuando existan usuarios reales) | 2 |
| V5 | `docker-compose.yml` publica la API en `0.0.0.0:8000` y la BD en `0.0.0.0:5432`: el backend es alcanzable sin pasar por el frontend. | Media | 4 |
| V6 | `PUT /me` y `DELETE /me` sin rate limiting; las Server Actions tampoco. | Baja (hardening) | 4 |

---

## 2. Supuestos y decisiones

| # | Decisión | Supuesto adoptado (pendiente de confirmar) | Alternativa |
|---|---|---|---|
| D1 | Default de `AUTH_MODE` | **SUPUESTO**: default `"disabled"`; `AUTH_MODE=demo` solo en `docker-compose.yml` de desarrollo. | Mantener `"demo"` y documentar (no cierra V1). |
| D2 | `DEMO_USER_ID` en producción | **SUPUESTO**: `getCurrentUserId()` ignora `DEMO_USER_ID` y `pfx_uid` si `NODE_ENV === "production"`, salvo `ALLOW_DEMO_USER=true` explícito. | Confiar solo en la configuración del despliegue. |
| D3 | `user_id` en el listado público | **SUPUESTO**: el listado público usa un schema sin `user_id` (`PublicRatingResponse`). | Eliminar `GET /courses/{id}/ratings` (el frontend no lo usa). |
| D4 | Auth real | **SUPUESTO**: JWT en cookie httpOnly emitido por el backend, tabla `users` con soft delete. Es la Fase 5.1 del plan 04. | Proveedor externo (Auth0, Clerk, NextAuth): cambia la Fase 3 entera. |
| D5 | Exposición de puertos | **SUPUESTO**: en producción solo el frontend es público; la API y la BD quedan en la red interna de Docker. En desarrollo se mantienen los puertos, ligados a `127.0.0.1`. | Reverse proxy delante de la API. |

---

## 3. Fases

Comandos base (siempre dentro del contenedor; antes, confirmar con `docker-compose ps` que `api` y `db` estén `Up`):

```bash
cd Backend && make start
make test
cd Frontend && npx yarn@1 test --run && npx yarn@1 lint && npx yarn@1 build
```

---

### Fase 1: Defaults seguros (cierra V1 y V2)

**Objetivo**: que un despliegue sin configuración explícita **no** acepte identidades falsas. El modo demo tiene que pedirse a propósito.

**Backend**
1. `app/core/config.py`: `auth_mode: str = "disabled"`. Documentar los valores válidos (`demo`, `disabled`, y en la Fase 3 `jwt`).
2. Validar `auth_mode` al arrancar (por ejemplo `Literal["demo", "disabled"]` en Pydantic Settings): un valor desconocido falla en el arranque en vez de dejar el sistema en un estado ambiguo.
3. `docker-compose.yml`: agregar `AUTH_MODE: demo` al servicio `api` (solo desarrollo).
4. Log de advertencia al arrancar si `auth_mode == "demo"`: "Modo demo: X-User-Id no autentica, no usar fuera de desarrollo".

**Frontend**
1. `src/lib/currentUser.ts`: si `process.env.NODE_ENV === "production"` y `ALLOW_DEMO_USER !== "true"`, devolver `null` (sin cookie ni `DEMO_USER_ID`). Con `null`, el detalle muestra "Inicia sesión para calificar este curso."
2. `Frontend/.env.example`: documentar `ALLOW_DEMO_USER` y aclarar que `DEMO_USER_ID` solo aplica en desarrollo.

**Tests**
- `test_rating_endpoints.py`: con `settings.auth_mode = "disabled"` (monkeypatch), `GET/PUT/DELETE /me` con header → 401 `UNAUTHENTICATED`.
- Test de settings: el default es `"disabled"` y un valor inválido lanza `ValidationError`.
- `src/lib/__tests__/currentUser.test.ts` (con `vi.mock('next/headers')` y `vi.mock('server-only')`): en producción sin `ALLOW_DEMO_USER` devuelve `null` aunque haya cookie y `DEMO_USER_ID`; en desarrollo respeta cookie > env; ids inválidos (`0`, `abc`, `-1`) → `null`.

**Verificación**: `make test`, `yarn test --run`. Manual: arrancar la API sin `AUTH_MODE` → `curl -X PUT .../ratings/me -H 'X-User-Id: 1'` responde 401; con `docker-compose` (demo) responde 201/200.
**Terminado cuando**: sin configuración explícita, ni el backend ni el frontend aceptan un usuario demo.
**Estimación**: 2 h.

---

### Fase 2: Minimizar datos expuestos (cierra V4)

**Objetivo**: que los endpoints públicos no revelen qué usuario votó qué.

**Backend**
1. `schemas/rating.py`: nuevo `PublicRatingResponse { id, course_id, rating, created_at, updated_at }` (sin `user_id`).
2. `routers/ratings.py`: `GET /courses/{course_id}/ratings` usa `response_model=List[PublicRatingResponse]`. `RatingResponse` (con `user_id`) queda solo para `/me`, donde el `user_id` es el del propio usuario.
3. Revisar que `/courses`, `/courses/{slug}` y `/stats` solo expongan agregados (hoy lo cumplen; dejar un test que lo fije).

**Frontend**
1. `src/types/rating.ts`: tipo `PublicCourseRating` sin `user_id`; `ratingsApi.getCourseRatings` lo usa. Hoy ninguna página lo consume; si se confirma D3-alternativa, eliminar la función.

**Tests**
- `test_rating_endpoints.py`: el listado público no contiene `user_id` (el set de campos es exactamente el de `PublicRatingResponse`), aunque el servicio lo devuelva.
- `TestRatingEndpointsContractCompliance` actualizado.

**Verificación**: `make test`; `curl localhost:8000/courses/<id>/ratings` sin `user_id`; `/docs` muestra el schema nuevo.
**Terminado cuando**: ningún endpoint sin autenticación devuelve `user_id` de terceros.
**Estimación**: 1.5 h.

---

### Fase 3: Autenticación real (cierra V3 y B4 definitivamente)

**Objetivo**: reemplazar `X-User-Id` por una identidad verificable. Todo pasa por `get_current_user_id()`, así que el resto de la aplicación no cambia.

**Backend**
1. Modelo `User` (hereda de `BaseModel`, soft delete): `email` único, `password_hash`, `name`. Migración con `make create-migration` + edición manual.
2. Hash de contraseñas con `argon2` (vía `passlib[argon2]` o `argon2-cffi`), agregado con `uv`.
3. `app/core/security.py`:
   - `create_access_token(user_id)` con expiración corta (p. ej. 30 min), `sub = user_id`, firmado con `settings.jwt_secret` (env, obligatorio si `auth_mode == "jwt"`; el arranque falla si falta o si mide menos de 32 bytes).
   - `get_current_user_id()`: en `auth_mode == "jwt"` valida firma, expiración y algoritmo fijo (`HS256`, nunca el `alg` que diga el token), y que el usuario exista y no esté borrado. El header `X-User-Id` se ignora.
4. `app/routers/auth.py`: `POST /auth/login` (respuesta genérica "credenciales inválidas" tanto si el email no existe como si la contraseña es incorrecta), `POST /auth/logout`, `GET /auth/me`.
5. Migración de datos: `course_ratings.user_id` → FK a `users.id`. Crear usuarios para los `user_id` existentes (seed) o limpiarlos; documentar la decisión en la migración.
6. `AUTH_MODE=demo` queda prohibido si `ENV=production` (validación al arrancar).

**Frontend**
1. Página `/login` + Server Action `login` que llama a `/auth/login` y guarda el token en una cookie `httpOnly`, `Secure`, `SameSite=Lax`, `Path=/`.
2. `src/lib/currentUser.ts`: deja de leer `pfx_uid`/`DEMO_USER_ID`; lee el token de la cookie de sesión. `ratingsApi` manda `Authorization: Bearer <token>` en vez de `X-User-Id`.
3. Las Server Actions (`rateCourse`, `removeRating`) siguen resolviendo el usuario en el servidor; si el backend responde 401, devuelven "Tu sesión expiró, inicia sesión de nuevo".
4. Logout: Server Action que borra la cookie.

**Tests**
- Tokens: válido, expirado, firma inválida, `alg: none`, `sub` de usuario borrado → 401.
- Login: credenciales correctas → cookie; incorrectas → 401 con mensaje genérico (mismo mensaje para email inexistente).
- `/me` ignora `X-User-Id` en modo `jwt`.
- Frontend: `currentUser` con cookie de sesión; acciones con 401 → mensaje de sesión expirada.

**Verificación**: `make test`, `yarn test --run`, `yarn build`. Manual: login → votar → logout → el formulario desaparece; `curl` con `X-User-Id` en modo `jwt` → 401.
**Terminado cuando**: no hay forma de actuar como otro usuario sin sus credenciales, y `X-User-Id`/`pfx_uid` ya no se usan en ningún camino.
**Estimación**: 12-16 h.

---

### Fase 4: Hardening de despliegue (cierra V5 y V6)

**Objetivo**: que el backend solo sea alcanzable a través del frontend en producción, y limitar el abuso de los endpoints de escritura.

**Infraestructura**
1. `docker-compose.yml` (desarrollo): publicar `127.0.0.1:8000:8000` y `127.0.0.1:5432:5432` en vez de todas las interfaces. Quitar el atributo obsoleto `version`.
2. Nuevo `docker-compose.prod.yml` (o documentación equivalente): la API y la BD sin `ports`, solo en la red interna; el frontend es el único servicio público. Credenciales de BD por env/secret, no las de desarrollo.
3. Documentar en `CLAUDE.md` y `Backend/README.md` la matriz de variables por entorno (`AUTH_MODE`, `JWT_SECRET`, `API_URL`, `ALLOW_DEMO_USER`).

**Backend**
1. Rate limiting en `PUT /me` y `DELETE /me` por usuario (p. ej. `slowapi`, 30 req/min), respondiendo 429 con `code: "RATE_LIMITED"` a través del handler de errores.
2. Desactivar `/docs` y `/openapi.json` en producción (`docs_url=None` si `ENV=production`).

**Frontend**
1. Cabeceras de seguridad en `next.config.ts` (`headers()`): `Content-Security-Policy` básica, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `frame-ancestors 'none'`.
2. Confirmar que las Server Actions mantienen la verificación de `Origin` de Next (no configurar `serverActions.allowedOrigins` con comodines).

**Tests**
- Backend: el request 31 en un minuto → 429 con `code`.
- Frontend: test de `next.config.ts` que verifica la presencia de las cabeceras.

**Verificación**: `make test`, `yarn build`; `ss -ltn` muestra 8000/5432 solo en `127.0.0.1`; `curl -I localhost:3000` muestra las cabeceras.
**Terminado cuando**: en producción la API no es alcanzable desde fuera de la red de Docker, las escrituras tienen límite y el frontend envía cabeceras de seguridad.
**Estimación**: 4-5 h.

---

## 4. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Cambiar el default de `AUTH_MODE` rompe el entorno de desarrollo de otros | `AUTH_MODE=demo` en `docker-compose.yml` y aviso en `CLAUDE.md` (Fase 1). |
| `NODE_ENV=production` en `yarn start` local desactiva el usuario demo | Documentar `ALLOW_DEMO_USER=true` en `.env.example` para smoke tests locales. |
| La migración de FK a `users` falla por `user_id` huérfanos | Crear usuarios para los ids existentes antes de la FK, dentro de la misma migración; backup previo (`pg_dump`). |
| Secreto JWT débil o filtrado | Validación de longitud al arrancar; secreto solo por env; rotación documentada (invalidar tokens cambiando el secreto). |
| Rate limiting en memoria no escala con varias réplicas | Aceptable con una réplica; con más, backend Redis para `slowapi`. |
| CSP rompe estilos o scripts de Next | Empezar con `Content-Security-Policy-Report-Only` y endurecer después. |

---

## 5. Checklist final

- [ ] Fase 1: `auth_mode` con default `"disabled"`, validado al arrancar; `AUTH_MODE=demo` solo en `docker-compose.yml`; aviso al arrancar en demo.
- [ ] Fase 1: `getCurrentUserId()` ignora cookie/`DEMO_USER_ID` en producción salvo `ALLOW_DEMO_USER=true`; `.env.example` actualizado.
- [ ] Fase 1: tests de `AUTH_MODE=disabled` → 401 y de `currentUser` en producción/desarrollo en verde.
- [ ] Fase 2: `GET /courses/{id}/ratings` sin `user_id` (`PublicRatingResponse`) y test de contrato.
- [ ] Fase 3: modelo `User` + migración + hash argon2; `POST /auth/login`, `/auth/logout`, `/auth/me`.
- [ ] Fase 3: `get_current_user_id()` valida JWT (firma, expiración, `alg` fijo, usuario activo); `X-User-Id` ignorado en modo `jwt`.
- [ ] Fase 3: `course_ratings.user_id` con FK a `users.id`; datos existentes migrados.
- [ ] Fase 3: frontend con login, cookie httpOnly/Secure/SameSite y `Authorization: Bearer`; `pfx_uid` eliminado.
- [ ] Fase 4: puertos de desarrollo en `127.0.0.1`; configuración de producción sin puertos para API y BD.
- [ ] Fase 4: rate limiting en `PUT`/`DELETE /me` con 429 `RATE_LIMITED`; `/docs` desactivado en producción.
- [ ] Fase 4: cabeceras de seguridad en `next.config.ts`.
- [ ] `make test`, `yarn test --run`, `yarn lint` y `yarn build` en verde al terminar cada fase.
- [ ] `CLAUDE.md` actualizado (modos de auth, variables por entorno, endpoints `/auth`).
- [ ] Decisiones D1-D5 confirmadas por el usuario (o el plan ajustado según la sección 2).

**Estimación total: ~20-25 h** (Fase 1: 2 h, Fase 2: 1.5 h, Fase 3: 12-16 h, Fase 4: 4-5 h).
