# Plan de Implementación: Sistema de Ratings Interactivo
# Platziflix — Multi-plataforma

**Fecha:** 2026-03-25
**Arquitecto:** Agent Architect
**Estado del Backend:** 100% completo, no modificar

---

## Resumen Ejecutivo

El backend ya expone 6 endpoints REST para ratings. La identidad del usuario se resuelve con
un UUID persistido localmente (sin auth). El trabajo restante es puramente de cliente: UI
interactiva en Frontend, display en iOS con navegación a detalle, y display + detalle en Android.

**Orden de implementación global:**
1. Frontend (infraestructura ya lista, menor riesgo, valida el flujo completo)
2. iOS (Clean Architecture establecida, necesita capas nuevas mínimas)
3. Android (mismo patrón que iOS, puede reusar decisiones)

---

## Restricción Crítica: Contrato de user_id

El backend espera `user_id: Int` (entero). La estrategia es generar un UUID, persistirlo
localmente y derivar un entero estable mediante `abs(uuid.hashCode())` en Android,
`abs(uuid.uuidString.hash)` en iOS, y `parseInt(uuid.replace(/-/g,'').slice(0,8), 16)` en
Frontend. Este entero se usa exclusivamente como identificador de sesión anónima — no cruza
entre plataformas ni tiene implicaciones de seguridad en este contexto.

---

## FASE 1 — Frontend (Next.js 15 + React 19 + TypeScript strict)

### Justificación del orden
Frontend tiene el 40% listo: `StarRating.tsx` (display), `ratingsApi.ts` (HTTP client),
`types/rating.ts` (tipos y guards). Solo faltan: gestión de identidad, componente interactivo
y la integración en la página de detalle. Es la plataforma con menor superficie de trabajo
nueva y permite validar el flujo completo contra el backend real antes de abordar mobile.

---

### Tarea F-1: Servicio de identidad de usuario

**Archivo a crear:**
`/home/renzo/claude-code/Frontend/src/services/userIdentity.ts`

**Responsabilidad:** Generar y persistir un `userId: number` anónimo en `localStorage`.
No debe ejecutarse en el servidor (Next.js SSR), por eso todas las funciones verifican
`typeof window !== 'undefined'`.

**Contrato de la función principal:**
```typescript
// Retorna el userId persistido. Si no existe, genera uno nuevo y lo persiste.
// Siempre retorna un entero positivo derivado de un UUID v4.
// Retorna null cuando se ejecuta en contexto de servidor.
export function getOrCreateUserId(): number | null
```

**Lógica interna:**
- Clave en localStorage: `'platziflix_user_id'`
- Si existe y es un número válido, retornarlo
- Si no existe: generar UUID con `crypto.randomUUID()`, calcular
  `parseInt(uuid.replace(/-/g,'').slice(0,8), 16)`, persistir y retornar
- El resultado siempre es un entero positivo en rango seguro de JavaScript

**Por qué `crypto.randomUUID()` y no una librería:** Disponible en browsers modernos y
en Node 14.17+. No agrega dependencias. Next.js 15 requiere Node 18+, por lo que es seguro.

---

### Tarea F-2: Componente interactivo de rating

**Archivo a crear:**
`/home/renzo/claude-code/Frontend/src/components/RatingInput/RatingInput.tsx`

**Archivo a crear:**
`/home/renzo/claude-code/Frontend/src/components/RatingInput/RatingInput.module.scss`

**Responsabilidad:** Estrellas clickeables para que el usuario envíe o actualice su rating.
Es un Client Component (`'use client'`) porque requiere estado interactivo y `localStorage`.

**Props:**
```typescript
interface RatingInputProps {
  courseId: number;
  // Callback invocado tras éxito, para actualizar el display del rating promedio
  onRatingSubmitted?: (newStats: RatingStats) => void;
  className?: string;
}
```

**Estado interno (hooks):**
- `hoveredStar: number | null` — estrella sobre la que está el cursor (1-5)
- `submittedRating: number | null` — rating del usuario ya enviado (cargado al montar)
- `isLoading: boolean` — durante el fetch inicial y durante el submit
- `submitState: RatingState` — `'idle' | 'loading' | 'success' | 'error'`
- `errorMessage: string | null`

**Ciclo de vida:**
1. Al montar: leer `userId` via `getOrCreateUserId()`. Si es null (SSR), no renderizar.
2. Con el `userId`, llamar `ratingsApi.getUserRating(courseId, userId)`.
   - Si retorna `CourseRating`: setear `submittedRating` con el valor existente.
   - Si retorna `null` (204): `submittedRating` queda en null.
3. Click en estrella `n`:
   - Setear `submitState = 'loading'`
   - Llamar `ratingsApi.createRating(courseId, { user_id: userId, rating: n })`
     (el backend hace upsert, por lo que no es necesario distinguir create vs update)
   - En éxito: setear `submittedRating = n`, `submitState = 'success'`,
     llamar `onRatingSubmitted` con los nuevos stats (obtenidos de otra llamada a
     `ratingsApi.getRatingStats` o del objeto retornado si el backend lo incluye)
   - En error: setear `submitState = 'error'`, `errorMessage`

**Renderizado:**
- 5 estrellas como botones `<button>` accesibles con `aria-label="Calificar con N estrellas"`
- Estado visual: estrella llena si `hoveredStar >= n` o (sin hover y `submittedRating >= n`)
- Mensaje de estado: "Tu calificación: N/5" tras éxito, o mensaje de error
- Durante carga: deshabilitar todos los botones con `disabled` y cambiar cursor
- `role="group"` en el contenedor con `aria-label="Calificar este curso"`

**Nota de accesibilidad:** Cada `<button>` debe tener `type="button"` para evitar submit
de formulario accidental. El estado de hover debe ser ignorado por lectores de pantalla
(`aria-hidden` en los SVG internos, el label está en el button).

---

### Tarea F-3: Integración en CourseDetail

**Archivos a modificar:**
- `/home/renzo/claude-code/Frontend/src/app/course/[slug]/page.tsx`
- `/home/renzo/claude-code/Frontend/src/components/CourseDetail/CourseDetail.tsx`

**Decisión arquitectural clave:** `CourseDetail.tsx` es actualmente un Server Component
(importado desde un Server Component page sin `'use client'`). `RatingInput` requiere
`'use client'`. La solución es NO convertir `CourseDetail.tsx` en Client Component —
en cambio, crear un wrapper client que se incruste dentro del layout de detalle.

**Archivo a crear:**
`/home/renzo/claude-code/Frontend/src/components/CourseRatingSection/CourseRatingSection.tsx`

**Responsabilidad:** Client Component que orquesta el display del rating promedio (usando
`StarRating` ya existente) junto con el `RatingInput` interactivo. Recibe `courseId` y
los stats iniciales como props serializables (SSR-safe).

**Props:**
```typescript
interface CourseRatingSectionProps {
  courseId: number;
  initialAverageRating: number;
  initialTotalRatings: number;
}
```

**Estado interno:**
- `averageRating: number` — inicializado con `initialAverageRating`
- `totalRatings: number` — inicializado con `initialTotalRatings`

Cuando `RatingInput` llama `onRatingSubmitted(newStats)`, este componente actualiza
`averageRating` y `totalRatings` sin re-fetch (optimistic-like: los nuevos stats vienen
del callback).

**Modificación en `CourseDetail.tsx`:**
Agregar `courseId` a `CourseDetailComponentProps`. Insertar `<CourseRatingSection>` dentro
del bloque `courseInfo`, después de los stats de duración/clases, antes del cierre del div.
El componente `CourseDetail.tsx` sigue siendo un Server Component — solo importa
`CourseRatingSection` que sí tiene `'use client'`. Next.js maneja esto correctamente.

**Modificación en `page.tsx`:**
- `getCourseData` ya retorna el objeto del backend que incluye `average_rating` y
  `total_ratings` (el endpoint `GET /courses/{slug}` los incluye).
- Pasar `course.id`, `course.average_rating`, `course.total_ratings` a
  `CourseDetailComponent`.
- Revisar el tipo `CourseDetail` en `/home/renzo/claude-code/Frontend/src/types/index.ts`
  y agregar `id: number`, `average_rating: number`, `total_ratings: number` si no existen.
- Cambiar la URL de fetch a usar `process.env.NEXT_PUBLIC_API_URL` en lugar del hardcode
  `http://localhost:8000` (el hardcode es un bug preexistente que conviene corregir aquí).

---

### Tarea F-4: Tests del componente RatingInput

**Archivo a crear:**
`/home/renzo/claude-code/Frontend/src/components/RatingInput/__tests__/RatingInput.test.tsx`

**Framework:** Vitest 3.2.3 + React Testing Library 16.3.0 (ya configurado en el proyecto).

**Casos a cubrir:**
1. Renderiza 5 botones de estrella
2. Al montar sin rating previo: todas las estrellas vacías
3. Al montar con rating previo (mock de `getUserRating`): muestra las estrellas correctas
4. Click en estrella 4: llama `createRating` con `{ rating: 4, user_id: <id> }`
5. Tras submit exitoso: muestra mensaje "Tu calificación: 4/5"
6. Error de red: muestra mensaje de error, no bloquea la UI indefinidamente
7. `isLoading = true` durante submit: botones deshabilitados

**Mocks necesarios:**
- `vi.mock('@/services/ratingsApi')` para `getUserRating`, `createRating`, `getRatingStats`
- `vi.mock('@/services/userIdentity')` para que `getOrCreateUserId` retorne un número fijo
  (ej: `12345`) en lugar de acceder a `localStorage`

---

### Tarea F-5: Tests de userIdentity

**Archivo a crear:**
`/home/renzo/claude-code/Frontend/src/services/__tests__/userIdentity.test.ts`

**Casos a cubrir:**
1. Primera llamada: genera UUID, lo persiste en `localStorage`, retorna número positivo
2. Segunda llamada: retorna el mismo número (persistencia)
3. En contexto sin `window` (simular SSR): retorna null
4. El entero generado está en rango válido (> 0, < Number.MAX_SAFE_INTEGER)

---

### Dependencias entre tareas Frontend

```
F-1 (userIdentity)
    └── F-2 (RatingInput) — consume getOrCreateUserId y ratingsApi
            └── F-3 (integración CourseDetail) — monta RatingInput + CourseRatingSection
                    └── F-4, F-5 (tests) — pueden desarrollarse en paralelo con F-3
```

---

### Casos edge Frontend

| Caso | Manejo |
|------|--------|
| SSR: `window` no disponible | `getOrCreateUserId()` retorna `null`, `RatingInput` retorna `null` en render (no monta) |
| Usuario califica por primera vez | `getUserRating` retorna `null` (204), `createRating` hace el POST, backend hace upsert |
| Usuario ya tiene rating | `getUserRating` retorna el rating previo, stars pre-seleccionadas, click actualiza via `createRating` (upsert del backend) |
| Error de red en carga inicial | No mostrar error crítico, mostrar `RatingInput` en estado vacío (degradación graceful) |
| Error de red en submit | Mostrar mensaje de error inline, mantener el rating anterior en UI |
| Timeout (10s definido en `ratingsApi`) | `ApiError` con code `'TIMEOUT'`, mostrar mensaje específico |
| `courseId` inválido o curso eliminado | El backend retorna 404, `getRatingStats` en `ratingsApi.ts` ya retorna `{ average_rating: 0, total_ratings: 0 }` por 404 |
| Doble click rápido | Deshabilitar botones durante `submitState === 'loading'` |

---

### Criterios de aceptación Frontend

- [ ] En `/course/[slug]`, el usuario ve el rating promedio del curso con el componente `StarRating` existente
- [ ] El usuario puede hacer click en 1-5 estrellas para calificar
- [ ] Si ya calificó (detectado via `getUserRating`), sus estrellas aparecen pre-seleccionadas al cargar
- [ ] Tras calificar, el promedio mostrado se actualiza sin recargar la página
- [ ] El componente no se renderiza en SSR (no genera errores de hidratación)
- [ ] TypeScript strict: sin `any`, sin errores de compilación
- [ ] Tests pasan con `yarn test`
- [ ] Accesibilidad: estrellas son operables con teclado (Tab + Enter/Space)

---

## FASE 2 — iOS (Swift + SwiftUI + Clean Architecture)

### Justificación del orden
iOS está en 0% para ratings pero tiene la arquitectura más completa y documentada del
proyecto. El `NetworkManager` ya soporta `request<T, U>(_:body:responseType:)` con body
encoding, lo que significa que POST y PUT están listos a nivel infraestructura. La decisión
de hacer iOS antes de Android permite establecer los patrones de Clean Architecture para
ratings que Android puede replicar directamente.

---

### Tarea I-1: Modelos de dominio para ratings

**Archivo a crear:**
`/home/renzo/claude-code/Mobile/PlatziFlixiOS/PlatziFlixiOS/Domain/Models/CourseRating.swift`

**Contenido:**
```swift
struct CourseRating: Identifiable, Equatable {
    let id: Int
    let courseId: Int
    let userId: Int
    let rating: Int  // 1-5
    let createdAt: Date?
    let updatedAt: Date?
}

struct RatingStats: Equatable {
    let averageRating: Double  // 0.0 - 5.0
    let totalRatings: Int

    static let empty = RatingStats(averageRating: 0.0, totalRatings: 0)
}

struct RatingRequest: Equatable {
    let userId: Int
    let rating: Int  // 1-5
}
```

**Nota:** `RatingRequest` vive en Domain (no en Data) porque es la intención del usuario,
no un detalle de transporte. El mapper lo convertirá a DTO para la capa de datos.

---

### Tarea I-2: Servicio de identidad de usuario

**Archivo a crear:**
`/home/renzo/claude-code/Mobile/PlatziFlixiOS/PlatziFlixiOS/Services/UserIdentityService.swift`

**Responsabilidad:** Gestionar el `userId` anónimo en `UserDefaults`.

**Contrato:**
```swift
final class UserIdentityService {
    static let shared = UserIdentityService()

    // Retorna el userId persistido. Si no existe, genera uno y lo persiste.
    var userId: Int { get }
}
```

**Lógica interna:**
- Clave en `UserDefaults`: `"platziflix_user_id"`
- Si existe un valor `Int` para esa clave, retornarlo
- Si no: generar `UUID()`, calcular `abs(uuid.uuidString.hashValue % Int.max)`,
  persistir con `UserDefaults.standard.set(value, forKey:)`, retornar
- `private init()` para forzar uso del singleton

**Por qué `hashValue`:** `UUID.uuidString` en Swift produce strings como
`"E621E1F8-C36C-495A-93FC-0C247A3E6E5F"`. El hash de este string en Swift es estable
dentro de la misma sesión pero NO entre sesiones (Swift randomiza hashes por proceso).
**Solución correcta:** parsear los primeros 8 caracteres del UUID como hex directamente,
igual que Frontend: `Int(uuid.uuidString.replacingOccurrences(of: "-", with: "").prefix(8), radix: 16) ?? 0`.
Esto sí es estable y determinista.

---

### Tarea I-3: DTOs para ratings

**Archivo a crear:**
`/home/renzo/claude-code/Mobile/PlatziFlixiOS/PlatziFlixiOS/Data/Entities/RatingDTO.swift`

**Contenido:**
```swift
struct CourseRatingDTO: Codable {
    let id: Int
    let courseId: Int
    let userId: Int
    let rating: Int
    let createdAt: String?
    let updatedAt: String?

    enum CodingKeys: String, CodingKey {
        case id
        case courseId = "course_id"
        case userId = "user_id"
        case rating
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

struct RatingStatsDTO: Codable {
    let averageRating: Double
    let totalRatings: Int

    enum CodingKeys: String, CodingKey {
        case averageRating = "average_rating"
        case totalRatings = "total_ratings"
    }
}

struct RatingRequestDTO: Codable {
    let userId: Int
    let rating: Int

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case rating
    }
}
```

**Nota sobre `CourseDTO` existente:** El endpoint `GET /courses` ya retorna
`average_rating` y `total_ratings`. Modificar `CourseDTO.swift` para agregar:
```swift
let averageRating: Double?
let totalRatings: Int?
// CodingKeys: averageRating = "average_rating", totalRatings = "total_ratings"
```
Ambos opcionales para no romper la compatibilidad con seeds que no los tengan.

---

### Tarea I-4: Mapper para ratings

**Archivo a crear:**
`/home/renzo/claude-code/Mobile/PlatziFlixiOS/PlatziFlixiOS/Data/Mapper/RatingMapper.swift`

**Funciones:**
```swift
enum RatingMapper {
    static func toDomain(_ dto: CourseRatingDTO) -> CourseRating
    static func toDomain(_ dto: RatingStatsDTO) -> RatingStats
    static func toDTO(_ request: RatingRequest) -> RatingRequestDTO
}
```

Sigue el patrón exacto de `CourseMapper.swift` y `TeacherMapper.swift` existentes.

---

### Tarea I-5: Endpoints de ratings

**Archivo a modificar:**
`/home/renzo/claude-code/Mobile/PlatziFlixiOS/PlatziFlixiOS/Data/Repositories/CourseAPIEndpoints.swift`

Agregar los siguientes casos al enum `CourseAPIEndpoints`:

```swift
case getRatingStats(Int)          // GET /courses/{id}/ratings/stats
case getUserRating(Int, Int)      // GET /courses/{id}/ratings/user/{userId}
case createRating(Int)            // POST /courses/{id}/ratings
case updateRating(Int, Int)       // PUT /courses/{id}/ratings/{userId}
case deleteRating(Int, Int)       // DELETE /courses/{id}/ratings/{userId}
```

En `var path`:
- `.getRatingStats(let id)`: `"/courses/\(id)/ratings/stats"`
- `.getUserRating(let id, let userId)`: `"/courses/\(id)/ratings/user/\(userId)"`
- `.createRating(let id)`: `"/courses/\(id)/ratings"`
- `.updateRating(let id, let userId)`: `"/courses/\(id)/ratings/\(userId)"`
- `.deleteRating(let id, let userId)`: `"/courses/\(id)/ratings/\(userId)"`

En `var method`:
- `.getRatingStats`, `.getUserRating`: `.GET`
- `.createRating`: `.POST`
- `.updateRating`: `.PUT`
- `.deleteRating`: `.DELETE`

**Nota sobre body:** El `APIEndpoint` protocol actual solo soporta body via la propiedad
`var body: Data?`. Los endpoints que requieren body (`createRating`, `updateRating`)
necesitan una estrategia. La solución limpia es usar el método
`NetworkManager.request<T, U>(_:body:responseType:)` ya existente, que acepta un
`Encodable` como body. El endpoint en sí no necesita el body (body es nil en el enum);
el ViewModel/Repository lo pasa al llamar al NetworkManager. Esto es consistente con
la arquitectura existente (`APIEndpointWithBody` es privado al NetworkManager).

---

### Tarea I-6: Repository protocol — extensión para ratings

**Archivo a modificar:**
`/home/renzo/claude-code/Mobile/PlatziFlixiOS/PlatziFlixiOS/Domain/Repositories/CourseRepositoryProtocol.swift`

Agregar al protocol `CourseRepository`:
```swift
func getRatingStats(courseId: Int) async throws -> RatingStats
func getUserRating(courseId: Int, userId: Int) async throws -> CourseRating?
func submitRating(courseId: Int, request: RatingRequest) async throws -> CourseRating
func deleteRating(courseId: Int, userId: Int) async throws
```

**Por qué `getUserRating` retorna `CourseRating?`:** El backend retorna 204 cuando el
usuario no ha calificado. El `NetworkManager` lanzará `NetworkError.requestFailed(204)`.
`RemoteCourseRepository` debe capturar ese caso específico y retornar `nil` en lugar
de propagar el error.

**Por qué `submitRating` en lugar de `createRating`/`updateRating`:** El backend hace
upsert en el POST. Una sola función en el cliente es más simple y correcto semánticamente.

---

### Tarea I-7: Implementación RemoteCourseRepository — ratings

**Archivo a modificar:**
`/home/renzo/claude-code/Mobile/PlatziFlixiOS/PlatziFlixiOS/Data/Repositories/RemoteCourseRepository.swift`

Implementar los 4 métodos nuevos del protocol. Los puntos clave:

- `getRatingStats`: Llama a `networkService.request(endpoint, responseType: RatingStatsDTO.self)`,
  mapea con `RatingMapper.toDomain(_:)`. Si el backend retorna 404 (curso sin ratings),
  retornar `RatingStats.empty`.

- `getUserRating`: Llama al endpoint, si el status es 204 retornar `nil` (capturar
  `NetworkError.requestFailed(204)` y retornar nil). Si 404, retornar nil también.

- `submitRating`: Llama a `networkService.request(endpoint, body: RatingMapper.toDTO(request), responseType: CourseRatingDTO.self)`. Mapea respuesta con `RatingMapper.toDomain(_:)`.

- `deleteRating`: Llama al endpoint con `.DELETE`. El backend retorna 204 (sin body).
  El NetworkManager lanzará error por 204 (está fuera del rango 200...299 que acepta).
  Solución: crear un método en el NetworkManager o en el Repository que acepte respuestas
  vacías. La opción más limpia es capturar `NetworkError.requestFailed(204)` en el
  Repository y tratarlo como éxito.

---

### Tarea I-8: CourseDetail — modelo de dominio extendido

**Archivo a modificar:**
`/home/renzo/claude-code/Mobile/PlatziFlixiOS/PlatziFlixiOS/Domain/Models/Course.swift`

Agregar al struct `Course`:
```swift
let averageRating: Double  // default 0.0
let totalRatings: Int      // default 0
```

Actualizar `CourseMapper.swift` para mapear los nuevos campos opcionales de `CourseDTO`
a los campos del domain model (con valores por defecto si son nil).

Actualizar las instancias mock en `Course.swift` para incluir los nuevos campos.

---

### Tarea I-9: Vista de StarRating reutilizable

**Archivo a crear:**
`/home/renzo/claude-code/Mobile/PlatziFlixiOS/PlatziFlixiOS/Presentation/Views/StarRatingView.swift`

**Responsabilidad:** Equivalente al `StarRating.tsx` de Frontend. Display-only, sin
interactividad. Sigue los patrones visuales de `DesignSystem.swift`.

**Parámetros:**
```swift
struct StarRatingView: View {
    let rating: Double      // 0.0 - 5.0
    let totalRatings: Int
    let showCount: Bool     // default true
    let starSize: CGFloat   // default 16
}
```

**Renderizado:** 5 estrellas usando `Image(systemName:)` de SF Symbols:
- `star.fill` para llena
- `star.leadinghalffilledutf8` (o `"star.lefthalf.fill"`) para media estrella
- `star` para vacía
Color: `Color.yellow` o usar el token de DesignSystem si existe uno para ratings.

---

### Tarea I-10: Vista de RatingInput interactiva

**Archivo a crear:**
`/home/renzo/claude-code/Mobile/PlatziFlixiOS/PlatziFlixiOS/Presentation/Views/RatingInputView.swift`

**Responsabilidad:** 5 estrellas clickeables para calificar. Necesita acceso al
`UserIdentityService` y al repository.

**Parámetros:**
```swift
struct RatingInputView: View {
    let courseId: Int
    let onRatingSubmitted: ((RatingStats) -> Void)?
    @StateObject private var viewModel: RatingInputViewModel
}
```

**ViewModel asociado — archivo a crear:**
`/home/renzo/claude-code/Mobile/PlatziFlixiOS/PlatziFlixiOS/Presentation/ViewModels/RatingInputViewModel.swift`

```swift
@MainActor
class RatingInputViewModel: ObservableObject {
    @Published var submittedRating: Int? = nil
    @Published var hoveredRating: Int? = nil
    @Published var isLoading: Bool = false
    @Published var errorMessage: String? = nil
    @Published var successMessage: String? = nil

    private let courseId: Int
    private let repository: CourseRepository
    private let userId: Int

    init(courseId: Int, repository: CourseRepository = RemoteCourseRepository())

    func loadUserRating() async
    func submitRating(_ rating: Int) async
}
```

`loadUserRating()` se llama en `.task {}` de la View al aparecer.
`submitRating(_:)` se llama al tap de estrella.

---

### Tarea I-11: Pantalla de detalle de curso (CourseDetailView)

Esta tarea estaba pendiente independientemente del sistema de ratings. Se implementa aquí
porque ratings necesitan vivir en la pantalla de detalle.

**Archivo a crear:**
`/home/renzo/claude-code/Mobile/PlatziFlixiOS/PlatziFlixiOS/Presentation/Views/CourseDetailView.swift`

**Archivo a crear:**
`/home/renzo/claude-code/Mobile/PlatziFlixiOS/PlatziFlixiOS/Presentation/ViewModels/CourseDetailViewModel.swift`

`CourseDetailViewModel`:
```swift
@MainActor
class CourseDetailViewModel: ObservableObject {
    @Published var course: Course?
    @Published var ratingStats: RatingStats = .empty
    @Published var isLoading: Bool = false
    @Published var errorMessage: String? = nil

    private let slug: String
    private let repository: CourseRepository

    init(slug: String, repository: CourseRepository = RemoteCourseRepository())

    func loadCourse() async  // llama getCourseBySlug + getRatingStats en paralelo con async let
}
```

`CourseDetailView` incluirá:
- Thumbnail de la imagen del curso
- Nombre, descripción
- `StarRatingView` con el promedio actual (se actualiza via callback de `RatingInputView`)
- `RatingInputView` para calificar
- Lista de clases (si el DTO las incluye)

**Navegación desde CourseListView:**
Modificar `CourseListView.swift` para envolver `CourseCardView` en un `NavigationLink` apuntando a `CourseDetailView(slug: course.slug)`.

Modificar `CourseListViewModel.swift`: el método `selectCourse(_:)` actualmente solo imprime.
En iOS la navegación se maneja con `NavigationLink` en la View, por lo que `selectCourse`
puede eliminarse o mantenerse como hook para analytics futuro.

---

### Dependencias entre tareas iOS

```
I-1 (modelos domain) ─────────────────────────────────────────────────────┐
I-2 (UserIdentityService) ────────────────────────────────────────────┐   │
I-3 (DTOs) → I-4 (Mapper) ──────────────────────────────────────────┐ │   │
I-5 (endpoints) → I-6 (protocol) → I-7 (RemoteRepo) ───────────────┤ │   │
                                                                     ↓ ↓   ↓
I-8 (Course domain update) ──────────────────────────────────────────────→ I-11 (CourseDetailView)
I-9 (StarRatingView) ────────────────────────────────────────────────────→ I-11
I-10 (RatingInputView + ViewModel) ─────────────────────────────────────→ I-11
```

---

### Casos edge iOS

| Caso | Manejo |
|------|--------|
| Backend retorna 204 para getUserRating | Capturar `requestFailed(204)` en Repository, retornar nil |
| Backend retorna 204 para deleteRating | Capturar `requestFailed(204)`, tratar como éxito |
| UUID hash negativo en Swift | Usar `abs()` o parsear directamente el hex del UUID string |
| Sin conexión al cargar detalle | `NetworkError.networkUnavailable` → mensaje en `CourseDetailViewModel.errorMessage` |
| Error en submit de rating | No cerrar la vista, mostrar error inline en `RatingInputViewModel.errorMessage` |
| Curso sin ratings (stats vacíos) | `RatingStats.empty` (averageRating: 0.0, totalRatings: 0), mostrar "Sin calificaciones" |

---

### Criterios de aceptación iOS

- [ ] La lista de cursos muestra el rating promedio con `StarRatingView` en cada `CourseCardView`
- [ ] Tap en un curso navega a `CourseDetailView`
- [ ] `CourseDetailView` carga el curso y sus stats de rating
- [ ] El usuario puede calificar con estrellas interactivas
- [ ] Si ya calificó, las estrellas aparecen pre-seleccionadas
- [ ] El promedio se actualiza en la vista tras calificar (sin navegar)
- [ ] Los estados de loading y error son visibles y claros
- [ ] Sigue el Design System existente (colores, tipografía, spacing de `DesignSystem.swift`)
- [ ] Compila sin warnings en Swift 5.9+

---

## FASE 3 — Android (Kotlin + Jetpack Compose + MVVM/MVI)

### Justificación del orden
Android tiene el mismo 0% de ratings que iOS pero su arquitectura es ligeramente menos
completa (falta detalle de curso, el `CourseDTO` es más simple). Al ir después de iOS, los
patrones de dominio ya están establecidos y solo hay que traducirlos al idioma de Kotlin.
Android tiene la ventaja del `USE_MOCK_DATA` flag que facilita el desarrollo aislado.

---

### Tarea A-1: Modelos de dominio para ratings

**Archivo a crear:**
`/home/renzo/claude-code/Mobile/PlatziFlixAndroid/app/src/main/java/com/espaciotiago/platziflixandroid/domain/models/CourseRating.kt`

```kotlin
data class CourseRating(
    val id: Int,
    val courseId: Int,
    val userId: Int,
    val rating: Int,  // 1-5
    val createdAt: String?,
    val updatedAt: String?
)

data class RatingStats(
    val averageRating: Double,  // 0.0 - 5.0
    val totalRatings: Int
) {
    companion object {
        val EMPTY = RatingStats(averageRating = 0.0, totalRatings = 0)
    }
}

data class RatingRequest(
    val userId: Int,
    val rating: Int  // 1-5
)
```

**Modificación en `Course.kt`:** Agregar campos opcionales:
```kotlin
val averageRating: Double = 0.0,
val totalRatings: Int = 0
```

---

### Tarea A-2: Servicio de identidad de usuario

**Archivo a crear:**
`/home/renzo/claude-code/Mobile/PlatziFlixAndroid/app/src/main/java/com/espaciotiago/platziflixandroid/data/local/UserIdentityManager.kt`

```kotlin
class UserIdentityManager(private val context: Context) {
    private val prefs = context.getSharedPreferences("platziflix_prefs", Context.MODE_PRIVATE)
    private val KEY = "user_id"

    fun getOrCreateUserId(): Int {
        val existing = prefs.getInt(KEY, -1)
        if (existing != -1) return existing

        val uuid = UUID.randomUUID().toString().replace("-", "")
        val userId = uuid.take(8).toInt(16)
        prefs.edit().putInt(KEY, userId).apply()
        return userId
    }
}
```

**Actualización en `AppModule.kt`:** Agregar:
```kotlin
fun provideUserIdentityManager(context: Context): UserIdentityManager {
    return UserIdentityManager(context)
}
```

`AppModule` necesita recibir `Context` para crear `UserIdentityManager`. Si `AppModule`
es un `object` (singleton), se puede inicializar en `MainActivity.onCreate` pasando
`applicationContext`.

---

### Tarea A-3: DTOs para ratings

**Archivo a crear:**
`/home/renzo/claude-code/Mobile/PlatziFlixAndroid/app/src/main/java/com/espaciotiago/platziflixandroid/data/entities/RatingDTO.kt`

```kotlin
data class CourseRatingDTO(
    @SerializedName("id") val id: Int,
    @SerializedName("course_id") val courseId: Int,
    @SerializedName("user_id") val userId: Int,
    @SerializedName("rating") val rating: Int,
    @SerializedName("created_at") val createdAt: String?,
    @SerializedName("updated_at") val updatedAt: String?
)

data class RatingStatsDTO(
    @SerializedName("average_rating") val averageRating: Double,
    @SerializedName("total_ratings") val totalRatings: Int
)

data class RatingRequestDTO(
    @SerializedName("user_id") val userId: Int,
    @SerializedName("rating") val rating: Int
)
```

**Modificación en `CourseDTO.kt`:** Agregar campos opcionales:
```kotlin
@SerializedName("average_rating") val averageRating: Double? = null,
@SerializedName("total_ratings") val totalRatings: Int? = null
```

---

### Tarea A-4: Mapper para ratings

**Archivo a crear:**
`/home/renzo/claude-code/Mobile/PlatziFlixAndroid/app/src/main/java/com/espaciotiago/platziflixandroid/data/mappers/RatingMapper.kt`

```kotlin
object RatingMapper {
    fun toDomain(dto: CourseRatingDTO): CourseRating
    fun toDomain(dto: RatingStatsDTO): RatingStats
    fun toDTO(request: RatingRequest): RatingRequestDTO
}
```

**Modificación en `CourseMapper.kt`:** Actualizar `toDomain(CourseDTO)` para mapear
`averageRating` y `totalRatings` (con `?: 0.0` y `?: 0` por ser opcionales).

---

### Tarea A-5: Endpoints de ratings en ApiService

**Archivo a modificar:**
`/home/renzo/claude-code/Mobile/PlatziFlixAndroid/app/src/main/java/com/espaciotiago/platziflixandroid/data/network/ApiService.kt`

Agregar:
```kotlin
@GET("courses/{id}/ratings/stats")
suspend fun getRatingStats(@Path("id") courseId: Int): Response<RatingStatsDTO>

@GET("courses/{id}/ratings/user/{userId}")
suspend fun getUserRating(
    @Path("id") courseId: Int,
    @Path("userId") userId: Int
): Response<CourseRatingDTO>

@POST("courses/{id}/ratings")
suspend fun createRating(
    @Path("id") courseId: Int,
    @Body request: RatingRequestDTO
): Response<CourseRatingDTO>

@PUT("courses/{id}/ratings/{userId}")
suspend fun updateRating(
    @Path("id") courseId: Int,
    @Path("userId") userId: Int,
    @Body request: RatingRequestDTO
): Response<CourseRatingDTO>

@DELETE("courses/{id}/ratings/{userId}")
suspend fun deleteRating(
    @Path("id") courseId: Int,
    @Path("userId") userId: Int
): Response<Unit>
```

**Nota sobre `getUserRating` y 204:** Retrofit con `Response<T>` permite inspeccionar el
status code sin lanzar excepción. `response.code() == 204` indica que el usuario no ha
calificado. `Response<CourseRatingDTO>` puede tener body null con status 204.

---

### Tarea A-6: Repository interface — ratings

**Archivo a modificar:**
`/home/renzo/claude-code/Mobile/PlatziFlixAndroid/app/src/main/java/com/espaciotiago/platziflixandroid/domain/repositories/CourseRepository.kt`

Agregar:
```kotlin
suspend fun getRatingStats(courseId: Int): Result<RatingStats>
suspend fun getUserRating(courseId: Int, userId: Int): Result<CourseRating?>
suspend fun submitRating(courseId: Int, request: RatingRequest): Result<CourseRating>
suspend fun deleteRating(courseId: Int, userId: Int): Result<Unit>
```

Mantener el patrón `Result<T>` existente. `getUserRating` retorna `Result<CourseRating?>`
donde `null` significa que el usuario no ha calificado (204 o 404).

---

### Tarea A-7: RemoteCourseRepository — ratings

**Archivo a modificar:**
`/home/renzo/claude-code/Mobile/PlatziFlixAndroid/app/src/main/java/com/espaciotiago/platziflixandroid/data/repositories/RemoteCourseRepository.kt`

Implementar los 4 nuevos métodos del interface. Puntos clave:

- Todas las funciones usan el patrón `runCatching { ... }` o try/catch retornando
  `Result.success(value)` / `Result.failure(exception)`, igual que `getAllCourses`.
- `getUserRating`: Si `response.code() == 204` o `response.code() == 404`,
  retornar `Result.success(null)`.
- `deleteRating`: Si `response.code() == 204`, retornar `Result.success(Unit)`.
- Siempre llamar a `RatingMapper.toDomain()` para mapear DTOs.

**MockCourseRepository:** Agregar implementaciones stub de los 4 métodos:
- `getRatingStats` retorna `Result.success(RatingStats.EMPTY)`
- `getUserRating` retorna `Result.success(null)`
- `submitRating` retorna `Result.success(CourseRating(id=1, ...))`
- `deleteRating` retorna `Result.success(Unit)`

---

### Tarea A-8: Componente StarRating en Compose

**Archivo a crear:**
`/home/renzo/claude-code/Mobile/PlatziFlixAndroid/app/src/main/java/com/espaciotiago/platziflixandroid/presentation/courses/components/StarRatingDisplay.kt`

```kotlin
@Composable
fun StarRatingDisplay(
    rating: Double,
    totalRatings: Int,
    showCount: Boolean = true,
    starSize: Dp = 16.dp,
    modifier: Modifier = Modifier
)
```

Usa `Icon(imageVector = Icons.Filled.Star, ...)` para estrellas llenas,
`Icons.Outlined.Star` para vacías. Para media estrella, usar un `Box` con dos íconos
superpuestos y un clip en el 50%.
Color: `Color(0xFFFFC107)` (Material amber) o el token del tema si existe.

**Modificación en `CourseCard.kt`:** Agregar `StarRatingDisplay` mostrando
`course.averageRating` y `course.totalRatings` (campos nuevos del domain model).

---

### Tarea A-9: Componente RatingInput en Compose

**Archivo a crear:**
`/home/renzo/claude-code/Mobile/PlatziFlixAndroid/app/src/main/java/com/espaciotiago/platziflixandroid/presentation/courses/components/RatingInput.kt`

```kotlin
@Composable
fun RatingInput(
    courseId: Int,
    viewModel: RatingInputViewModel,
    modifier: Modifier = Modifier
)
```

Usa `IconButton` de Material 3 para cada estrella. Estado visual igual que iOS:
hover/seleccionado = `Icons.Filled.Star`, sin seleccionar = `Icons.Outlined.Star`.

**ViewModel asociado — archivo a crear:**
`/home/renzo/claude-code/Mobile/PlatziFlixAndroid/app/src/main/java/com/espaciotiago/platziflixandroid/presentation/courses/viewmodel/RatingInputViewModel.kt`

Sigue el patrón MVI del `CourseListViewModel` existente:
```kotlin
data class RatingInputUiState(
    val submittedRating: Int? = null,
    val isLoading: Boolean = false,
    val error: String? = null,
    val successMessage: String? = null
)

sealed class RatingInputUiEvent {
    data class SubmitRating(val rating: Int) : RatingInputUiEvent()
    object LoadUserRating : RatingInputUiEvent()
    object ClearError : RatingInputUiEvent()
}

class RatingInputViewModel(
    private val courseId: Int,
    private val courseRepository: CourseRepository,
    private val userIdentityManager: UserIdentityManager
) : ViewModel()
```

---

### Tarea A-10: Pantalla de detalle de curso

**Archivo a crear:**
`/home/renzo/claude-code/Mobile/PlatziFlixAndroid/app/src/main/java/com/espaciotiago/platziflixandroid/presentation/courses/screen/CourseDetailScreen.kt`

**Archivo a crear:**
`/home/renzo/claude-code/Mobile/PlatziFlixAndroid/app/src/main/java/com/espaciotiago/platziflixandroid/presentation/courses/state/CourseDetailUiState.kt`

**Archivo a crear:**
`/home/renzo/claude-code/Mobile/PlatziFlixAndroid/app/src/main/java/com/espaciotiago/platziflixandroid/presentation/courses/viewmodel/CourseDetailViewModel.kt`

Extensión del repository para `getCourseBySlug`:
**Archivo a modificar:** `CourseRepository.kt` — agregar:
```kotlin
suspend fun getCourseBySlug(slug: String): Result<Course>
```

**Archivo a modificar:** `ApiService.kt` — agregar:
```kotlin
@GET("courses/{slug}")
suspend fun getCourseBySlug(@Path("slug") slug: String): Response<CourseDetailDTO>
```

**Archivo a crear:**
`/home/renzo/claude-code/Mobile/PlatziFlixAndroid/app/src/main/java/com/espaciotiago/platziflixandroid/data/entities/CourseDetailDTO.kt`

```kotlin
data class CourseDetailDTO(
    @SerializedName("id") val id: Int,
    @SerializedName("name") val name: String,
    // ... campos base más:
    @SerializedName("average_rating") val averageRating: Double?,
    @SerializedName("total_ratings") val totalRatings: Int?,
    @SerializedName("lessons") val lessons: List<LessonDTO>?
)

data class LessonDTO(
    @SerializedName("id") val id: Int,
    @SerializedName("name") val name: String,
    @SerializedName("slug") val slug: String
)
```

**Navegación:** Modificar `CourseListScreen.kt` para que el click en `CourseCard`
dispare un evento de navegación. Modificar `MainActivity.kt` para usar `NavHost`
con rutas `"courses"` y `"course/{slug}"`.

**Actualización en `AppModule.kt`:** Agregar `provideCourseDetailViewModel(slug)` y
`provideRatingInputViewModel(courseId)`.

---

### Dependencias entre tareas Android

```
A-1 (domain models) ─────────────────────────────────────────────────────┐
A-2 (UserIdentityManager) ───────────────────────────────────────────┐   │
A-3 (DTOs) → A-4 (Mapper) ─────────────────────────────────────────┐ │   │
A-5 (ApiService) → A-6 (Repository interface) → A-7 (RemoteRepo) ──┤ │   │
                                                                    ↓ ↓   ↓
A-8 (StarRatingDisplay) ────────────────────────────────────────────────→ A-10 (CourseDetailScreen)
A-9 (RatingInput + ViewModel) ──────────────────────────────────────────→ A-10
```

---

### Casos edge Android

| Caso | Manejo |
|------|--------|
| Retrofit 204 sin body | `Response<CourseRatingDTO>` con `response.code() == 204`, body será null |
| `toInt(16)` overflow | UUID hex primeros 8 chars = max `0xFFFFFFFF` = 4294967295, mayor que `Int.MAX_VALUE`. Usar `.toLong(16).and(0x7FFFFFFF).toInt()` para asegurar positivo |
| `USE_MOCK_DATA = true` | Mock retorna datos hardcodeados, permite desarrollo sin backend |
| Sin conexión | OkHttpClient timeout 30s, `IOException` capturada en Repository → `Result.failure` → error en UiState |
| Contexto en AppModule | AppModule object necesita `applicationContext` para `UserIdentityManager`; inicializar en `Application.onCreate()` o en `MainActivity` |

---

### Criterios de aceptación Android

- [ ] La lista de cursos muestra el rating promedio en cada tarjeta con `StarRatingDisplay`
- [ ] Tap en una tarjeta navega a `CourseDetailScreen`
- [ ] `CourseDetailScreen` muestra la información del curso y permite calificar
- [ ] Si el usuario ya calificó, las estrellas están pre-seleccionadas
- [ ] El promedio se actualiza localmente tras calificar (sin volver a la lista)
- [ ] `USE_MOCK_DATA = true` funciona para las nuevas funcionalidades
- [ ] Los estados loading/error siguen el patrón `CourseListUiState` (MVI)
- [ ] Compila sin warnings en Kotlin 1.9+

---

## Tabla Resumen de Archivos

### Frontend — archivos nuevos
| Archivo | Tipo | Tarea |
|---------|------|-------|
| `src/services/userIdentity.ts` | Nuevo | F-1 |
| `src/components/RatingInput/RatingInput.tsx` | Nuevo | F-2 |
| `src/components/RatingInput/RatingInput.module.scss` | Nuevo | F-2 |
| `src/components/CourseRatingSection/CourseRatingSection.tsx` | Nuevo | F-3 |
| `src/components/RatingInput/__tests__/RatingInput.test.tsx` | Nuevo | F-4 |
| `src/services/__tests__/userIdentity.test.ts` | Nuevo | F-5 |

### Frontend — archivos modificados
| Archivo | Cambio | Tarea |
|---------|--------|-------|
| `src/app/course/[slug]/page.tsx` | Pasar `id`, `average_rating`, `total_ratings` a `CourseDetailComponent`; fix hardcode URL | F-3 |
| `src/components/CourseDetail/CourseDetail.tsx` | Recibir `courseId`, montar `CourseRatingSection` | F-3 |
| `src/types/index.ts` | Agregar `id`, `average_rating`, `total_ratings` al tipo `CourseDetail` | F-3 |

### iOS — archivos nuevos
| Archivo | Tipo | Tarea |
|---------|------|-------|
| `Domain/Models/CourseRating.swift` | Nuevo | I-1 |
| `Services/UserIdentityService.swift` | Nuevo | I-2 |
| `Data/Entities/RatingDTO.swift` | Nuevo | I-3 |
| `Data/Mapper/RatingMapper.swift` | Nuevo | I-4 |
| `Presentation/Views/StarRatingView.swift` | Nuevo | I-9 |
| `Presentation/Views/RatingInputView.swift` | Nuevo | I-10 |
| `Presentation/ViewModels/RatingInputViewModel.swift` | Nuevo | I-10 |
| `Presentation/Views/CourseDetailView.swift` | Nuevo | I-11 |
| `Presentation/ViewModels/CourseDetailViewModel.swift` | Nuevo | I-11 |

### iOS — archivos modificados
| Archivo | Cambio | Tarea |
|---------|--------|-------|
| `Data/Repositories/CourseAPIEndpoints.swift` | Agregar 5 casos de rating | I-5 |
| `Domain/Repositories/CourseRepositoryProtocol.swift` | Agregar 4 métodos de rating | I-6 |
| `Data/Repositories/RemoteCourseRepository.swift` | Implementar 4 métodos de rating | I-7 |
| `Domain/Models/Course.swift` | Agregar `averageRating`, `totalRatings` | I-8 |
| `Data/Entities/CourseDTO.swift` | Agregar campos de rating opcionales | I-3 |
| `Data/Mapper/CourseMapper.swift` | Mapear nuevos campos | I-8 |
| `Presentation/Views/CourseCardView.swift` | Agregar `StarRatingView` | I-9 |
| `Presentation/Views/CourseListView.swift` | Agregar `NavigationLink` a detalle | I-11 |

### Android — archivos nuevos
| Archivo | Tipo | Tarea |
|---------|------|-------|
| `domain/models/CourseRating.kt` | Nuevo | A-1 |
| `data/local/UserIdentityManager.kt` | Nuevo | A-2 |
| `data/entities/RatingDTO.kt` | Nuevo | A-3 |
| `data/entities/CourseDetailDTO.kt` | Nuevo | A-10 |
| `data/mappers/RatingMapper.kt` | Nuevo | A-4 |
| `presentation/courses/components/StarRatingDisplay.kt` | Nuevo | A-8 |
| `presentation/courses/components/RatingInput.kt` | Nuevo | A-9 |
| `presentation/courses/viewmodel/RatingInputViewModel.kt` | Nuevo | A-9 |
| `presentation/courses/screen/CourseDetailScreen.kt` | Nuevo | A-10 |
| `presentation/courses/state/CourseDetailUiState.kt` | Nuevo | A-10 |
| `presentation/courses/viewmodel/CourseDetailViewModel.kt` | Nuevo | A-10 |

### Android — archivos modificados
| Archivo | Cambio | Tarea |
|---------|--------|-------|
| `data/network/ApiService.kt` | Agregar 5 endpoints de rating + getCourseBySlug | A-5, A-10 |
| `domain/repositories/CourseRepository.kt` | Agregar 4 métodos de rating + getCourseBySlug | A-6, A-10 |
| `data/repositories/RemoteCourseRepository.kt` | Implementar nuevos métodos | A-7, A-10 |
| `data/repositories/MockCourseRepository.kt` | Implementar stubs de nuevos métodos | A-7 |
| `data/entities/CourseDTO.kt` | Agregar `averageRating`, `totalRatings` opcionales | A-3 |
| `data/mappers/CourseMapper.kt` | Mapear nuevos campos de rating | A-4 |
| `domain/models/Course.kt` | Agregar `averageRating`, `totalRatings` | A-1 |
| `di/AppModule.kt` | Agregar `UserIdentityManager`, nuevos ViewModels | A-2, A-9, A-10 |
| `presentation/courses/components/CourseCard.kt` | Agregar `StarRatingDisplay` | A-8 |
| `presentation/courses/screen/CourseListScreen.kt` | Agregar navegación a detalle | A-10 |
| `MainActivity.kt` | Implementar NavHost con rutas | A-10 |

---

## Notas de Arquitectura Transversales

### Por qué usar upsert (POST) en lugar de create/update diferenciados
El endpoint `POST /courses/{id}/ratings` del backend hace upsert automático. Esto significa
que el cliente nunca necesita verificar si existe un rating previo antes de enviar: siempre
llama al mismo endpoint. La llamada a `getUserRating` al montar el componente es únicamente
para pre-poblar la UI con el valor existente, no para decidir qué endpoint llamar.

### Por qué no implementar deleteRating en la UI inicial
El backend expone DELETE pero la especificación de producto no requiere que el usuario
pueda eliminar su calificación en esta iteración. El Repository implementa el método
(por completitud del contrato) pero ningún componente de UI lo invoca. Esto es
intencionalmente correcto.

### Por qué los stats se actualizan localmente tras el submit
Tras un submit exitoso, el componente podría: (a) re-fetchar los stats del servidor,
o (b) usar los stats que retorna el backend en la respuesta del POST. El backend
de Platziflix no retorna los stats actualizados en el POST de rating (retorna el
`CourseRating` creado). Por lo tanto, la opción correcta es hacer una llamada adicional
a `GET /courses/{id}/ratings/stats` tras el submit exitoso para obtener el promedio
actualizado. Esta segunda llamada debe hacerse en el background, sin bloquear la UI.

### Consistencia del userId entre sesiones
El UUID se genera una vez y se persiste indefinidamente en el almacenamiento local.
Si el usuario borra la app o limpia localStorage, se genera un nuevo UUID y sus ratings
anteriores quedan huérfanos en la base de datos (sin forma de reclamarlos). Este es el
comportamiento aceptado dado que no hay autenticación. Los ratings huérfanos son soft-deleted
cuando el usuario nuevo interactúa, no afectan las estadísticas históricas.
