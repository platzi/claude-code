# Plan de Implementación Frontend: Sistema de Ratings para Platziflix

**Versión**: 1.0
**Fecha**: 2025-10-14
**Alcance**: Frontend (Next.js 15 + TypeScript)
**Estimación**: 8 horas
**Stack**: Next.js 15, React 19, TypeScript, SCSS, Vitest

---

## Contexto del Proyecto

### Arquitectura Frontend Actual
- **Framework**: Next.js 15 con App Router
- **React**: 19.0 (componentes funcionales + hooks)
- **TypeScript**: Strict mode habilitado
- **Estilos**: SCSS con CSS Modules
- **Testing**: Vitest + React Testing Library + @testing-library/jest-dom
- **Patrones**: Server Components para pages, Client Components para interactividad

### Estructura de Componentes Existente
```
Frontend/src/
├── app/                        # App Router pages
│   ├── course/[slug]/          # Página de detalle de curso
│   └── page.tsx                # Home con grid de cursos
├── components/
│   ├── Course/                 # Card de curso (usado en grid)
│   │   ├── Course.tsx
│   │   ├── Course.module.scss
│   │   └── __test__/
│   ├── CourseDetail/           # Vista completa de curso
│   │   ├── CourseDetail.tsx
│   │   └── CourseDetail.module.scss
│   └── VideoPlayer/            # Reproductor de video
└── types/
    └── index.ts                # Tipos globales
```

### Patrones de Desarrollo Identificados
1. **Props typing**: Uso de `Omit`, interfaces específicas
2. **Fetch pattern**: Server Components hacen fetch directo al backend
3. **Error handling**: Pages con error.tsx, loading.tsx, not-found.tsx
4. **CSS Modules**: Estilos con naming `.module.scss`
5. **Testing**: Tests en carpeta `__test__` dentro del componente

---

## FASE 1: TypeScript Types & Interfaces

**Duración estimada**: 30 minutos
**Archivo**: `Frontend/src/types/index.ts`

### 1.1 Nuevas Interfaces para Ratings

#### CourseRating Interface
```typescript
export interface CourseRating {
  id: number;
  course_id: number;
  user_id: number;
  rating: number;           // 1-5
  created_at: string;       // ISO 8601
  updated_at: string;       // ISO 8601
}
```

**Consideraciones**:
- `course_id` y `user_id` mantienen snake_case por compatibilidad con backend
- `rating` es número entero validado en backend (1-5)
- Timestamps como strings para serialización JSON
- No incluir `deleted_at` en frontend (manejo interno del backend)

#### RatingRequest Interface
```typescript
export interface RatingRequest {
  user_id: number;
  rating: number;           // 1-5
}
```

**Consideraciones**:
- Payload mínimo para POST/PUT requests
- Validación del rango 1-5 será responsabilidad del componente
- `user_id` será hardcoded temporalmente hasta implementar autenticación

#### RatingStats Interface
```typescript
export interface RatingStats {
  average_rating: number;   // Promedio calculado (0.0 - 5.0)
  total_ratings: number;    // Cantidad total de ratings
}
```

**Consideraciones**:
- `average_rating` puede ser 0 si no hay ratings
- Usado para mostrar estadísticas agregadas
- Calculado por el backend

### 1.2 Actualizar Interface Course

**Cambios en la interface existente**:
```typescript
export interface Course {
  id: number;
  title: string;
  teacher: string;
  duration: number;
  thumbnail: string;
  slug: string;

  // Nuevos campos opcionales
  average_rating?: number;  // 0.0 - 5.0
  total_ratings?: number;   // Cantidad de ratings
}
```

**Consideraciones**:
- Campos opcionales (`?`) porque no siempre vendrán del backend
- Mantener retrocompatibilidad con componentes existentes
- El backend puede no enviar estos campos en todos los endpoints

### 1.3 Estados de UI (Loading, Error)

#### RatingState Type
```typescript
export type RatingState = 'idle' | 'loading' | 'success' | 'error';
```

**Uso**:
- Controlar estados de submit de rating
- Mostrar spinners, disabled states, mensajes de error

#### RatingError Interface
```typescript
export interface RatingError {
  message: string;
  code?: string;
  details?: Record<string, unknown>;
}
```

**Consideraciones**:
- Estructura para errores consistentes
- `code` puede ser HTTP status o error code custom
- `details` para información adicional de debug

### 1.4 Validaciones TypeScript

**Type Guards para validación runtime**:
```typescript
export function isValidRating(rating: number): rating is number {
  return Number.isInteger(rating) && rating >= 1 && rating <= 5;
}

export function isCourseRating(obj: unknown): obj is CourseRating {
  // Runtime validation para responses del backend
}
```

**Consideraciones**:
- Type guards para validar datos del backend
- Evitar `any` en toda la implementación
- Validación en runtime complementa TypeScript compile-time

---

## FASE 2: API Service Layer

**Duración estimada**: 1.5 horas
**Archivo nuevo**: `Frontend/src/services/ratingsApi.ts`

### 2.1 Configuración del Service

#### Environment Variables
**Archivo**: `.env.local` (crear si no existe)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Consideraciones**:
- Prefijo `NEXT_PUBLIC_` para variables accesibles en cliente
- Valor por defecto en el código si no está definida
- Documentar en README que esta variable es requerida

#### Base Configuration
```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface FetchOptions extends RequestInit {
  timeout?: number;
}

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'ApiError';
  }
}
```

**Consideraciones**:
- Clase `ApiError` customizada para errores HTTP
- `FetchOptions` extiende `RequestInit` de fetch nativo
- Timeout opcional para prevenir requests colgados
- No usar librerías externas (axios, etc) para mantener bundle pequeño

### 2.2 Helper Functions

#### fetchWithTimeout
```typescript
async function fetchWithTimeout(
  url: string,
  options: FetchOptions = {}
): Promise<Response> {
  const { timeout = 10000, ...fetchOptions } = options;

  // Implementar AbortController para timeout
  // Lanzar ApiError en caso de timeout o network error
  // Validar response.ok y parsear errores del backend
}
```

**Consideraciones**:
- Timeout por defecto: 10 segundos
- Usar `AbortController` para cancelar requests
- Manejar network errors (offline, DNS failure, etc)
- Parsear errores JSON del backend

#### handleApiResponse
```typescript
async function handleApiResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    // Parsear error del backend
    // Lanzar ApiError con información apropiada
  }

  return response.json() as Promise<T>;
}
```

**Consideraciones**:
- Validar content-type JSON antes de parsear
- Extraer mensaje de error del body si existe
- Manejar diferentes códigos HTTP (400, 404, 500, etc)
- Type-safe con generics

### 2.3 Ratings API Methods

#### getCourseRatings
```typescript
async function getCourseRatings(courseId: number): Promise<CourseRating[]> {
  // GET /courses/{course_id}/ratings
  // Retornar array vacío si 404
  // Lanzar error en otros casos
}
```

**Especificación**:
- **Endpoint**: `GET /courses/{courseId}/ratings`
- **Response**: Array de `CourseRating`
- **Error handling**:
  - 404 → retornar `[]` (no ratings aún)
  - 500 → lanzar `ApiError`
- **Use case**: Cargar ratings existentes en CourseDetail

#### addCourseRating
```typescript
async function addCourseRating(
  courseId: number,
  data: RatingRequest
): Promise<CourseRating> {
  // POST /courses/{course_id}/ratings
  // Body: { user_id, rating }
  // Validar rating antes de enviar
}
```

**Especificación**:
- **Endpoint**: `POST /courses/{courseId}/ratings`
- **Body**: `{ user_id: number, rating: number }`
- **Headers**: `Content-Type: application/json`
- **Response**: Objeto `CourseRating` creado
- **Validación previa**:
  - `isValidRating(data.rating)` antes de hacer request
  - `user_id > 0`
- **Error handling**:
  - 400 → datos inválidos (mostrar mensaje al usuario)
  - 409 → rating ya existe para ese usuario
  - 500 → error del servidor

#### updateCourseRating
```typescript
async function updateCourseRating(
  courseId: number,
  userId: number,
  data: RatingRequest
): Promise<CourseRating> {
  // PUT /courses/{course_id}/ratings/{user_id}
  // Body: { user_id, rating }
}
```

**Especificación**:
- **Endpoint**: `PUT /courses/{courseId}/ratings/{userId}`
- **Body**: `{ user_id: number, rating: number }`
- **Response**: Objeto `CourseRating` actualizado
- **Use case**: Usuario cambia su rating existente
- **Error handling**:
  - 404 → rating no existe (usar addCourseRating en su lugar)
  - 400 → datos inválidos

#### deleteCourseRating
```typescript
async function deleteCourseRating(
  courseId: number,
  userId: number
): Promise<void> {
  // DELETE /courses/{course_id}/ratings/{user_id}
  // No retorna contenido (204)
}
```

**Especificación**:
- **Endpoint**: `DELETE /courses/{courseId}/ratings/{userId}`
- **Response**: 204 No Content
- **Use case**: Usuario elimina su rating
- **Error handling**:
  - 404 → rating no existe (ignorar o mostrar mensaje)
  - 500 → error del servidor

#### getCourseWithRatings
```typescript
async function getCourseWithRatings(slug: string): Promise<CourseDetail> {
  // Wrapper sobre el fetch existente
  // Asegurar que incluya average_rating y total_ratings
}
```

**Especificación**:
- **Endpoint**: `GET /courses/{slug}` (existente)
- **Response**: `CourseDetail` con campos de rating
- **Consideración**: El backend debe incluir los campos agregados
- **Fallback**: Si no vienen, inicializar en 0

### 2.4 Export del Service

```typescript
export const ratingsApi = {
  getCourseRatings,
  addCourseRating,
  updateCourseRating,
  deleteCourseRating,
  getCourseWithRatings,
} as const;

export { ApiError };
```

**Consideraciones**:
- Export como objeto constante para tree-shaking
- Exportar `ApiError` para manejo en componentes
- Mantener API limpia y funciones privadas internas

### 2.5 Testing del Service

**Archivo**: `Frontend/src/services/__tests__/ratingsApi.test.ts`

**Tests requeridos**:
- Construcción correcta de URLs
- Manejo de timeouts
- Parseo de errores HTTP
- Validación de ratings (1-5)
- Headers correctos en requests
- Manejo de network errors

**Consideraciones**:
- Usar `vi.mock` para mockear `fetch`
- No hacer requests reales al backend
- Validar error messages sean informativos

---

## FASE 3: StarRating Component

**Duración estimada**: 2.5 horas
**Archivos**:
- `Frontend/src/components/StarRating/StarRating.tsx`
- `Frontend/src/components/StarRating/StarRating.module.scss`
- `Frontend/src/components/StarRating/__tests__/StarRating.test.tsx`

### 3.1 Props Interface

```typescript
interface StarRatingProps {
  rating: number;                              // Valor actual (0-5, puede ser decimal)
  onRatingChange?: (rating: number) => void;   // Callback para cambios
  readonly?: boolean;                          // Modo solo lectura
  size?: 'small' | 'medium' | 'large';         // Tamaño visual
  showCount?: boolean;                         // Mostrar cantidad de ratings
  totalRatings?: number;                       // Número total de ratings
  disabled?: boolean;                          // Deshabilitar interacción
  className?: string;                          // Clase CSS adicional
  userId?: number;                             // Para marcar si usuario ya calificó
}
```

**Valores por defecto**:
```typescript
const {
  rating,
  onRatingChange,
  readonly = false,
  size = 'medium',
  showCount = false,
  totalRatings = 0,
  disabled = false,
  className = '',
  userId,
} = props;
```

### 3.2 Estados Internos del Componente

```typescript
const [hoverRating, setHoverRating] = useState<number>(0);
const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
```

**Comportamiento de estados**:
- `hoverRating`: Rating temporal mientras el mouse está sobre las estrellas
- `isSubmitting`: True durante API call (deshabilita interacción)
- **Modo readonly**: No usar estados de hover
- **Modo disabled**: Deshabilitar eventos de hover y click

### 3.3 Funcionalidad Interactiva

#### Event Handlers

**handleMouseEnter**:
```typescript
const handleMouseEnter = (star: number) => {
  if (readonly || disabled || isSubmitting) return;
  setHoverRating(star);
};
```

**handleMouseLeave**:
```typescript
const handleMouseLeave = () => {
  if (readonly || disabled || isSubmitting) return;
  setHoverRating(0);
};
```

**handleClick**:
```typescript
const handleClick = (star: number) => {
  if (readonly || disabled || isSubmitting || !onRatingChange) return;
  onRatingChange(star);
};
```

**handleKeyDown** (accesibilidad):
```typescript
const handleKeyDown = (event: React.KeyboardEvent, star: number) => {
  if (readonly || disabled || isSubmitting) return;

  // Arrow Right/Left: navegar entre estrellas
  // Enter/Space: seleccionar rating
  // Escape: cancelar (deshacer hover)
};
```

### 3.4 Renderizado de Estrellas

#### Cálculo de estado visual de cada estrella
```typescript
const getStarFillState = (starIndex: number): 'empty' | 'half' | 'full' => {
  const currentRating = hoverRating || rating;

  if (currentRating >= starIndex) return 'full';
  if (currentRating >= starIndex - 0.5) return 'half';
  return 'empty';
};
```

**Consideraciones**:
- Soportar medias estrellas para display (no para selección)
- Priorizar `hoverRating` sobre `rating` para feedback visual
- Modo readonly: solo mostrar `rating`, ignorar hover

#### JSX Structure
```typescript
return (
  <div
    className={`${styles.starRating} ${styles[size]} ${className}`}
    role="group"
    aria-label={`Rating: ${rating} out of 5 stars`}
  >
    <div className={styles.stars}>
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          className={`${styles.star} ${styles[getStarFillState(star)]}`}
          onClick={() => handleClick(star)}
          onMouseEnter={() => handleMouseEnter(star)}
          onMouseLeave={handleMouseLeave}
          onKeyDown={(e) => handleKeyDown(e, star)}
          disabled={readonly || disabled || isSubmitting}
          aria-label={`Rate ${star} stars`}
          aria-pressed={rating === star}
          tabIndex={readonly ? -1 : 0}
        >
          <StarIcon fillState={getStarFillState(star)} />
        </button>
      ))}
    </div>

    {showCount && totalRatings > 0 && (
      <span className={styles.count} aria-label={`${totalRatings} ratings`}>
        ({totalRatings})
      </span>
    )}
  </div>
);
```

### 3.5 StarIcon Sub-component

```typescript
interface StarIconProps {
  fillState: 'empty' | 'half' | 'full';
}

const StarIcon = ({ fillState }: StarIconProps) => {
  // SVG inline para control completo del estilo
  // Usar clip-path o linearGradient para medias estrellas
  // Tres variantes: empty, half, full
};
```

**Consideraciones**:
- SVG inline para evitar requests adicionales
- `viewBox="0 0 24 24"` para escalar correctamente
- `currentColor` para heredar color del CSS
- Implementar half-star con `clipPath` o `linearGradient`

### 3.6 CSS Modules (StarRating.module.scss)

#### Estructura de estilos
```scss
.starRating {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;

  .stars {
    display: flex;
    gap: 0.125rem;
  }

  .star {
    border: none;
    background: transparent;
    padding: 0;
    cursor: pointer;
    transition: transform 0.2s ease, color 0.2s ease;
    color: var(--star-empty-color, #e0e0e0);

    &:hover:not(:disabled) {
      transform: scale(1.1);
    }

    &:focus-visible {
      outline: 2px solid var(--focus-color, #4a90e2);
      outline-offset: 2px;
      border-radius: 2px;
    }

    &:disabled {
      cursor: not-allowed;
      opacity: 0.6;
    }

    &.full {
      color: var(--star-full-color, #ffc107);
    }

    &.half {
      color: var(--star-half-color, #ffc107);
      // Implementar gradient para media estrella
    }
  }

  .count {
    margin-left: 0.5rem;
    font-size: 0.875em;
    color: var(--text-secondary, #666);
  }

  // Size variants
  &.small {
    .star svg { width: 16px; height: 16px; }
  }

  &.medium {
    .star svg { width: 24px; height: 24px; }
  }

  &.large {
    .star svg { width: 32px; height: 32px; }
  }
}
```

**Consideraciones de diseño**:
- Usar CSS variables para fácil theming
- Transiciones suaves (200ms) para hover y transform
- Focus visible para accesibilidad (teclado)
- Cursor pointer solo en modo interactivo
- Disabled state con opacity reducida
- Responsive: sizes se adaptan a mobile

### 3.7 Accesibilidad (a11y)

#### Atributos ARIA
- `role="group"` en el container
- `aria-label` descriptivo del rating actual
- `aria-pressed` en el botón de la estrella seleccionada
- `aria-label` en cada botón indicando el rating
- `tabIndex={-1}` en modo readonly (no navegable por teclado)

#### Navegación por teclado
- **Tab**: Navegar entre estrellas
- **Arrow Left/Right**: Mover entre estrellas
- **Enter/Space**: Seleccionar rating
- **Escape**: Cancelar (resetear hover)

#### Screen readers
- Anunciar cambio de rating con `aria-live="polite"`
- Feedback audible al seleccionar rating
- Contador de ratings accesible

### 3.8 Variantes y Casos de Uso

#### Readonly Display (Course Card)
```typescript
<StarRating
  rating={4.5}
  readonly={true}
  size="small"
  showCount={true}
  totalRatings={128}
/>
```

#### Interactive Rating (Course Detail)
```typescript
<StarRating
  rating={userRating}
  onRatingChange={handleRatingChange}
  size="large"
  disabled={isSubmitting}
/>
```

#### Loading State
```typescript
<StarRating
  rating={userRating}
  onRatingChange={handleRatingChange}
  disabled={true}  // Durante API call
/>
```

---

## FASE 4: Integration en Course Components

**Duración estimada**: 2 horas
**Archivos modificados**:
- `Frontend/src/components/Course/Course.tsx`
- `Frontend/src/components/Course/Course.module.scss`
- `Frontend/src/components/CourseDetail/CourseDetail.tsx`
- `Frontend/src/components/CourseDetail/CourseDetail.module.scss`
- `Frontend/src/app/course/[slug]/page.tsx` (Client Component nuevo)

### 4.1 Actualizar Course Component (Card View)

#### Props Update
```typescript
type CourseProps = Omit<CourseType, "slug"> & {
  averageRating?: number;
  totalRatings?: number;
};
```

**Consideraciones**:
- Hacer opcionales los campos de rating (retrocompatibilidad)
- No romper componentes existentes que no envían estos props

#### JSX Changes
```typescript
export const Course = ({
  id,
  title,
  teacher,
  duration,
  thumbnail,
  averageRating,
  totalRatings
}: CourseProps) => {
  return (
    <article className={styles.courseCard}>
      <div className={styles.thumbnailContainer}>
        <img src={thumbnail} alt={title} className={styles.thumbnail} />
      </div>
      <div className={styles.courseInfo}>
        <h2 className={styles.courseTitle}>{title}</h2>
        <p className={styles.teacher}>Profesor: {teacher}</p>
        <p className={styles.duration}>Duración: {duration} minutos</p>

        {/* Nueva sección de rating */}
        {typeof averageRating === 'number' && (
          <div className={styles.ratingContainer}>
            <StarRating
              rating={averageRating}
              readonly={true}
              size="small"
              showCount={true}
              totalRatings={totalRatings}
            />
          </div>
        )}
      </div>
    </article>
  );
};
```

**Consideraciones**:
- Renderizado condicional: solo mostrar si `averageRating` existe
- Check estricto con `typeof averageRating === 'number'` (puede ser 0)
- Modo readonly: no es interactivo en el card
- Size small para mantener card compacto

#### SCSS Updates
```scss
// Course.module.scss
.courseCard {
  // ... estilos existentes ...

  .ratingContainer {
    margin-top: 0.75rem;
    padding-top: 0.75rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }
}
```

**Consideraciones de diseño**:
- Separador visual sutil (border-top)
- Spacing consistente con el resto del card
- No romper el layout en mobile

### 4.2 Actualizar CourseDetail Component

**Problema**: `CourseDetailComponent` actualmente es Server Component, pero necesitamos interactividad para ratings.

**Solución**: Crear Client Component para la sección de ratings.

#### Nuevo archivo: RatingSection.tsx (Client Component)

**Archivo**: `Frontend/src/components/CourseDetail/RatingSection.tsx`

```typescript
'use client';

import { useState } from 'react';
import { StarRating } from '@/components/StarRating/StarRating';
import { ratingsApi, ApiError } from '@/services/ratingsApi';
import type { CourseRating } from '@/types';
import styles from './RatingSection.module.scss';

interface RatingSectionProps {
  courseId: number;
  initialAverageRating?: number;
  initialTotalRatings?: number;
  userId: number;  // Temporal: hardcoded hasta auth
}

export const RatingSection = ({
  courseId,
  initialAverageRating = 0,
  initialTotalRatings = 0,
  userId,
}: RatingSectionProps) => {
  // ... implementación ...
};
```

#### Estados del componente
```typescript
const [userRating, setUserRating] = useState<number>(0);
const [averageRating, setAverageRating] = useState(initialAverageRating);
const [totalRatings, setTotalRatings] = useState(initialTotalRatings);
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState<string | null>(null);
const [successMessage, setSuccessMessage] = useState<string | null>(null);
```

**Consideraciones**:
- `userRating`: Rating actual del usuario (cargado al montar)
- `averageRating` y `totalRatings`: Actualizados optimistically
- `isLoading`: Deshabilita interacción durante API call
- `error` y `successMessage`: Feedback temporal al usuario

#### useEffect: Cargar rating del usuario
```typescript
useEffect(() => {
  const loadUserRating = async () => {
    try {
      setIsLoading(true);
      const ratings = await ratingsApi.getCourseRatings(courseId);
      const userRatingData = ratings.find(r => r.user_id === userId);

      if (userRatingData) {
        setUserRating(userRatingData.rating);
      }
    } catch (err) {
      console.error('Failed to load user rating:', err);
      // No mostrar error al usuario (no crítico)
    } finally {
      setIsLoading(false);
    }
  };

  loadUserRating();
}, [courseId, userId]);
```

**Consideraciones**:
- Solo cargar al montar el componente
- No bloquear UI si falla (no crítico)
- Guardar rating del usuario localmente

#### Handler: Cambio de rating
```typescript
const handleRatingChange = async (newRating: number) => {
  // 1. Guardar estado previo para rollback
  const previousRating = userRating;
  const previousAverage = averageRating;
  const previousTotal = totalRatings;

  try {
    // 2. Optimistic update
    setUserRating(newRating);
    setIsLoading(true);
    setError(null);

    // 3. Calcular nuevo promedio localmente (optimistic)
    const isNewRating = previousRating === 0;
    const newTotal = isNewRating ? previousTotal + 1 : previousTotal;
    const newAverage = calculateOptimisticAverage(
      previousAverage,
      previousTotal,
      previousRating,
      newRating,
      isNewRating
    );

    setAverageRating(newAverage);
    setTotalRatings(newTotal);

    // 4. Submit al backend
    const result = previousRating === 0
      ? await ratingsApi.addCourseRating(courseId, { user_id: userId, rating: newRating })
      : await ratingsApi.updateCourseRating(courseId, userId, { user_id: userId, rating: newRating });

    // 5. Success feedback
    setSuccessMessage('Rating guardado exitosamente');
    setTimeout(() => setSuccessMessage(null), 3000);

    // 6. Opcional: Refetch para sincronizar con backend
    // En producción, el backend devuelve los datos actualizados

  } catch (err) {
    // 7. Rollback en caso de error
    setUserRating(previousRating);
    setAverageRating(previousAverage);
    setTotalRatings(previousTotal);

    const errorMessage = err instanceof ApiError
      ? err.message
      : 'Error al guardar rating. Por favor intenta de nuevo.';

    setError(errorMessage);
    setTimeout(() => setError(null), 5000);

  } finally {
    setIsLoading(false);
  }
};
```

**Consideraciones clave**:
- **Optimistic Updates**: Actualizar UI inmediatamente
- **Rollback Strategy**: Revertir cambios si falla el API call
- **Feedback temporal**: Mensajes desaparecen automáticamente
- **Diferenciar ADD vs UPDATE**: Usar endpoint correcto
- **Error handling**: Mensajes informativos al usuario

#### Helper: Cálculo optimistic del promedio
```typescript
function calculateOptimisticAverage(
  currentAverage: number,
  currentTotal: number,
  oldRating: number,
  newRating: number,
  isNewRating: boolean
): number {
  if (isNewRating) {
    // Agregar nuevo rating
    const sum = currentAverage * currentTotal + newRating;
    return sum / (currentTotal + 1);
  } else {
    // Actualizar rating existente
    const sum = currentAverage * currentTotal - oldRating + newRating;
    return sum / currentTotal;
  }
}
```

**Consideraciones**:
- Matemática precisa para mantener consistencia
- Manejar edge case: `currentTotal === 0`
- Redondear a 1 decimal para display

#### JSX del RatingSection
```typescript
return (
  <section className={styles.ratingSection}>
    <div className={styles.userRating}>
      <h3 className={styles.title}>Califica este curso</h3>
      <StarRating
        rating={userRating}
        onRatingChange={handleRatingChange}
        size="large"
        disabled={isLoading}
      />

      {isLoading && (
        <p className={styles.loadingText}>Guardando...</p>
      )}

      {error && (
        <p className={styles.errorText} role="alert">
          {error}
        </p>
      )}

      {successMessage && (
        <p className={styles.successText} role="status">
          {successMessage}
        </p>
      )}
    </div>

    <div className={styles.ratingsStats}>
      <h4 className={styles.statsTitle}>Rating general</h4>
      <StarRating
        rating={averageRating}
        readonly={true}
        size="medium"
        showCount={true}
        totalRatings={totalRatings}
      />
      <p className={styles.statsDescription}>
        Basado en {totalRatings} {totalRatings === 1 ? 'valoración' : 'valoraciones'}
      </p>
    </div>
  </section>
);
```

**Consideraciones de UX**:
- Dos secciones claras: rating del usuario + estadísticas
- Feedback visual para todos los estados (loading, error, success)
- `role="alert"` para errores (screen readers)
- `role="status"` para mensajes de éxito
- Texto de loading simple durante submit

#### SCSS del RatingSection
```scss
// RatingSection.module.scss
.ratingSection {
  margin-top: 2rem;
  padding: 2rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;

  .userRating {
    margin-bottom: 2rem;
    padding-bottom: 2rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);

    .title {
      font-size: 1.25rem;
      margin-bottom: 1rem;
    }

    .loadingText {
      margin-top: 0.5rem;
      font-size: 0.875rem;
      color: var(--text-secondary, #999);
    }

    .errorText {
      margin-top: 0.5rem;
      padding: 0.5rem;
      background: rgba(244, 67, 54, 0.1);
      color: #f44336;
      border-radius: 4px;
      font-size: 0.875rem;
    }

    .successText {
      margin-top: 0.5rem;
      padding: 0.5rem;
      background: rgba(76, 175, 80, 0.1);
      color: #4caf50;
      border-radius: 4px;
      font-size: 0.875rem;
    }
  }

  .ratingsStats {
    .statsTitle {
      font-size: 1rem;
      margin-bottom: 0.75rem;
      font-weight: 500;
    }

    .statsDescription {
      margin-top: 0.5rem;
      font-size: 0.875rem;
      color: var(--text-secondary, #999);
    }
  }
}
```

**Consideraciones de diseño**:
- Background sutil para destacar sección
- Separador visual entre user rating y stats
- Colores semánticos: rojo (error), verde (success)
- Padding y spacing consistentes
- Responsive: ajustar padding en mobile

### 4.3 Integrar RatingSection en CourseDetail

**Cambios en**: `Frontend/src/components/CourseDetail/CourseDetail.tsx`

```typescript
import { RatingSection } from './RatingSection';

export const CourseDetailComponent: FC<CourseDetailComponentProps> = ({ course }) => {
  // ... código existente ...

  return (
    <div className={styles.container}>
      {/* ... contenido existente ... */}

      {/* Nueva sección de ratings */}
      <RatingSection
        courseId={course.id}
        initialAverageRating={course.average_rating}
        initialTotalRatings={course.total_ratings}
        userId={1}  // TODO: Reemplazar con userId real de auth
      />

      {/* Sección de clases existente */}
      <div className={styles.classesSection}>
        {/* ... contenido existente ... */}
      </div>
    </div>
  );
};
```

**Consideraciones**:
- `userId={1}` hardcoded temporalmente (comentario TODO)
- Posición: después del header, antes de las clases
- Props iniciales vienen del Server Component (SSR)

### 4.4 Actualizar Page para incluir datos de rating

**Cambios en**: `Frontend/src/app/course/[slug]/page.tsx`

```typescript
async function getCourseData(slug: string): Promise<CourseDetail> {
  const response = await fetch(`http://localhost:8000/courses/${slug}`, {
    cache: "no-store",
  });

  if (response.status === 404) {
    notFound();
  }

  if (!response.ok) {
    throw new Error("Failed to fetch course data");
  }

  const data = await response.json();

  // Asegurar que los campos de rating existan
  return {
    ...data,
    average_rating: data.average_rating ?? 0,
    total_ratings: data.total_ratings ?? 0,
  };
}
```

**Consideraciones**:
- Backend debe incluir `average_rating` y `total_ratings` en el response
- Fallback a 0 si no vienen del backend
- Mantener `cache: "no-store"` para datos frescos
- TypeScript validará que `CourseDetail` incluya estos campos

---

## FASE 5: State Management & UX Refinements

**Duración estimada**: 1 hora

### 5.1 Manejo de Estados Complejos

#### Estado de sincronización
```typescript
type SyncState = 'synced' | 'pending' | 'error';

const [syncState, setSyncState] = useState<SyncState>('synced');
```

**Uso**:
- `synced`: Rating guardado correctamente en backend
- `pending`: Esperando respuesta del backend
- `error`: Falló el submit, mostrar retry button

#### Indicador visual de sincronización
```typescript
{syncState === 'pending' && (
  <span className={styles.syncIndicator}>
    <Spinner size="small" /> Guardando...
  </span>
)}

{syncState === 'error' && (
  <button onClick={retrySubmit} className={styles.retryButton}>
    <RetryIcon /> Reintentar
  </button>
)}
```

### 5.2 Debouncing de Cambios

**Problema**: Usuario puede hacer hover rápido sobre varias estrellas, generando múltiples re-renders.

**Solución**: No implementar debounce en StarRating (feedback inmediato es UX prioritaria). El API call solo ocurre en click.

**Consideración alternativa**: Si se implementa rating por hover (sin click), usar debounce de 500ms.

### 5.3 Caché Local de Ratings

**Opcional**: Guardar rating del usuario en localStorage para evitar API calls en cada visita.

```typescript
// Al cargar componente
useEffect(() => {
  const cachedRating = localStorage.getItem(`rating_${courseId}_${userId}`);
  if (cachedRating) {
    setUserRating(Number(cachedRating));
  } else {
    loadUserRatingFromApi();
  }
}, []);

// Al guardar rating
const handleRatingChange = async (newRating: number) => {
  // ... API call ...
  localStorage.setItem(`rating_${courseId}_${userId}`, String(newRating));
};
```

**Consideraciones**:
- Validar que localStorage esté disponible (SSR-safe)
- Invalidar caché después de cierto tiempo
- No bloquear si localStorage no está disponible

### 5.4 Feedback Visual Mejorado

#### Animación de submit exitoso
```scss
@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.successAnimation {
  animation: pulse 0.3s ease-out;
}
```

#### Tooltip de confirmación
```typescript
{successMessage && (
  <div className={styles.tooltip} role="status">
    <CheckIcon /> {successMessage}
  </div>
)}
```

### 5.5 Performance Optimizations

#### Memoización del StarRating
```typescript
import { memo } from 'react';

export const StarRating = memo(({
  rating,
  onRatingChange,
  readonly,
  // ... otros props
}: StarRatingProps) => {
  // ... implementación ...
}, (prevProps, nextProps) => {
  // Custom comparison: solo re-render si rating cambia
  return prevProps.rating === nextProps.rating &&
         prevProps.disabled === nextProps.disabled &&
         prevProps.readonly === nextProps.readonly;
});
```

**Consideraciones**:
- Solo memoizar si hay problemas de performance
- Custom comparator para evitar re-renders innecesarios
- No memoizar si el componente es ligero (overhead no vale la pena)

#### Lazy loading del RatingSection
```typescript
import dynamic from 'next/dynamic';

const RatingSection = dynamic(
  () => import('./RatingSection').then(mod => ({ default: mod.RatingSection })),
  { loading: () => <RatingSectionSkeleton /> }
);
```

**Consideraciones**:
- Reducir bundle inicial de la página
- Mostrar skeleton mientras carga
- Solo útil si RatingSection es pesado (muchas dependencias)

### 5.6 Error Recovery Strategies

#### Retry automático
```typescript
const MAX_RETRIES = 3;
const [retryCount, setRetryCount] = useState(0);

const submitWithRetry = async (rating: number) => {
  try {
    await ratingsApi.addCourseRating(courseId, { user_id: userId, rating });
    setRetryCount(0); // Reset en éxito
  } catch (err) {
    if (retryCount < MAX_RETRIES && err instanceof ApiError && err.status >= 500) {
      // Retry solo en errores del servidor
      setRetryCount(prev => prev + 1);
      setTimeout(() => submitWithRetry(rating), 1000 * retryCount);
    } else {
      // Falló definitivamente
      handleError(err);
    }
  }
};
```

**Consideraciones**:
- Solo retry en errores 5xx (servidor)
- Exponential backoff: 1s, 2s, 3s
- No retry en errores 4xx (cliente)

#### Offline detection
```typescript
useEffect(() => {
  const handleOnline = () => {
    // Usuario volvió online, retry pendiente
    if (syncState === 'error') {
      retrySubmit();
    }
  };

  window.addEventListener('online', handleOnline);
  return () => window.removeEventListener('online', handleOnline);
}, [syncState]);
```

---

## FASE 6: Testing Frontend

**Duración estimada**: 1.5 horas

### 6.1 StarRating Component Tests

**Archivo**: `Frontend/src/components/StarRating/__tests__/StarRating.test.tsx`

#### Test Suite Structure
```typescript
describe('StarRating Component', () => {
  describe('Rendering', () => {
    // Tests de renderizado básico
  });

  describe('Interactivity', () => {
    // Tests de interacción (click, hover)
  });

  describe('Accessibility', () => {
    // Tests de a11y
  });

  describe('Props Variants', () => {
    // Tests de diferentes configuraciones
  });
});
```

#### Tests de Renderizado
```typescript
it('renders correct number of stars', () => {
  render(<StarRating rating={3} />);
  const stars = screen.getAllByRole('button');
  expect(stars).toHaveLength(5);
});

it('displays rating count when showCount is true', () => {
  render(<StarRating rating={4} showCount={true} totalRatings={42} />);
  expect(screen.getByText('(42)')).toBeInTheDocument();
});

it('does not display rating count when showCount is false', () => {
  render(<StarRating rating={4} showCount={false} totalRatings={42} />);
  expect(screen.queryByText('(42)')).not.toBeInTheDocument();
});

it('applies correct size class', () => {
  const { container } = render(<StarRating rating={3} size="large" />);
  expect(container.firstChild).toHaveClass('large');
});
```

#### Tests de Interactividad
```typescript
it('calls onRatingChange when star is clicked', async () => {
  const handleChange = vi.fn();
  render(<StarRating rating={0} onRatingChange={handleChange} />);

  const stars = screen.getAllByRole('button');
  await userEvent.click(stars[2]); // Click on 3rd star

  expect(handleChange).toHaveBeenCalledWith(3);
});

it('does not call onRatingChange when readonly', async () => {
  const handleChange = vi.fn();
  render(<StarRating rating={3} onRatingChange={handleChange} readonly={true} />);

  const stars = screen.getAllByRole('button');
  await userEvent.click(stars[4]);

  expect(handleChange).not.toHaveBeenCalled();
});

it('does not call onRatingChange when disabled', async () => {
  const handleChange = vi.fn();
  render(<StarRating rating={3} onRatingChange={handleChange} disabled={true} />);

  const stars = screen.getAllByRole('button');
  await userEvent.click(stars[4]);

  expect(handleChange).not.toHaveBeenCalled();
});

it('updates hover state on mouse enter and leave', async () => {
  const { container } = render(<StarRating rating={2} />);
  const stars = screen.getAllByRole('button');

  await userEvent.hover(stars[3]); // Hover over 4th star
  // Verificar que las primeras 4 estrellas tengan clase 'full'

  await userEvent.unhover(stars[3]);
  // Verificar que vuelva al rating original (2 estrellas)
});
```

#### Tests de Accesibilidad
```typescript
it('has correct ARIA labels', () => {
  render(<StarRating rating={3.5} totalRatings={10} />);

  expect(screen.getByRole('group')).toHaveAttribute(
    'aria-label',
    'Rating: 3.5 out of 5 stars'
  );

  const stars = screen.getAllByRole('button');
  stars.forEach((star, index) => {
    expect(star).toHaveAttribute('aria-label', `Rate ${index + 1} stars`);
  });
});

it('supports keyboard navigation', async () => {
  const handleChange = vi.fn();
  render(<StarRating rating={0} onRatingChange={handleChange} />);

  const stars = screen.getAllByRole('button');

  stars[0].focus();
  await userEvent.keyboard('{ArrowRight}');
  expect(stars[1]).toHaveFocus();

  await userEvent.keyboard('{Enter}');
  expect(handleChange).toHaveBeenCalledWith(2);
});

it('is not keyboard navigable when readonly', () => {
  render(<StarRating rating={3} readonly={true} />);

  const stars = screen.getAllByRole('button');
  stars.forEach(star => {
    expect(star).toHaveAttribute('tabIndex', '-1');
  });
});

it('has visible focus indicator', () => {
  render(<StarRating rating={3} />);

  const stars = screen.getAllByRole('button');
  stars[0].focus();

  // Verificar estilos de :focus-visible (requiere CSS-in-JS o snapshot)
});
```

#### Tests de Edge Cases
```typescript
it('handles rating of 0 correctly', () => {
  render(<StarRating rating={0} />);
  // Todas las estrellas deben estar vacías
});

it('handles decimal ratings correctly', () => {
  render(<StarRating rating={3.7} />);
  // Primeras 3 estrellas full, 4ta half, resto empty
});

it('clamps rating to 0-5 range', () => {
  render(<StarRating rating={7} />); // Rating inválido
  // Debe mostrar 5 estrellas full (no crash)
});

it('handles missing totalRatings gracefully', () => {
  render(<StarRating rating={4} showCount={true} />);
  expect(screen.getByText('(0)')).toBeInTheDocument();
});
```

### 6.2 RatingSection Integration Tests

**Archivo**: `Frontend/src/components/CourseDetail/__tests__/RatingSection.test.tsx`

#### Setup: Mock API
```typescript
import { vi } from 'vitest';
import * as ratingsApi from '@/services/ratingsApi';

vi.mock('@/services/ratingsApi', () => ({
  ratingsApi: {
    getCourseRatings: vi.fn(),
    addCourseRating: vi.fn(),
    updateCourseRating: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    constructor(message: string, public status: number) {
      super(message);
    }
  },
}));
```

#### Tests de Renderizado
```typescript
it('renders initial rating stats correctly', () => {
  render(
    <RatingSection
      courseId={1}
      initialAverageRating={4.2}
      initialTotalRatings={85}
      userId={1}
    />
  );

  expect(screen.getByText(/Basado en 85 valoraciones/)).toBeInTheDocument();
});

it('loads user rating on mount', async () => {
  const mockRatings = [
    { id: 1, course_id: 1, user_id: 1, rating: 4, created_at: '', updated_at: '' },
  ];

  vi.mocked(ratingsApi.ratingsApi.getCourseRatings).mockResolvedValue(mockRatings);

  render(<RatingSection courseId={1} userId={1} />);

  await waitFor(() => {
    expect(ratingsApi.ratingsApi.getCourseRatings).toHaveBeenCalledWith(1);
  });

  // Verificar que el rating del usuario se muestra
});
```

#### Tests de Interacción
```typescript
it('submits new rating successfully', async () => {
  const mockResponse = {
    id: 1,
    course_id: 1,
    user_id: 1,
    rating: 5,
    created_at: '2025-01-01',
    updated_at: '2025-01-01',
  };

  vi.mocked(ratingsApi.ratingsApi.addCourseRating).mockResolvedValue(mockResponse);

  render(<RatingSection courseId={1} userId={1} initialTotalRatings={10} />);

  const stars = screen.getAllByRole('button', { name: /Rate \d stars/ });
  await userEvent.click(stars[4]); // Click 5th star

  await waitFor(() => {
    expect(ratingsApi.ratingsApi.addCourseRating).toHaveBeenCalledWith(1, {
      user_id: 1,
      rating: 5,
    });
  });

  expect(screen.getByText(/Rating guardado exitosamente/)).toBeInTheDocument();
});

it('updates existing rating successfully', async () => {
  // Usuario ya tiene rating 3
  const initialRatings = [
    { id: 1, course_id: 1, user_id: 1, rating: 3, created_at: '', updated_at: '' },
  ];

  vi.mocked(ratingsApi.ratingsApi.getCourseRatings).mockResolvedValue(initialRatings);

  const mockResponse = { ...initialRatings[0], rating: 5 };
  vi.mocked(ratingsApi.ratingsApi.updateCourseRating).mockResolvedValue(mockResponse);

  render(<RatingSection courseId={1} userId={1} />);

  await waitFor(() => {
    expect(ratingsApi.ratingsApi.getCourseRatings).toHaveBeenCalled();
  });

  const stars = screen.getAllByRole('button', { name: /Rate \d stars/ });
  await userEvent.click(stars[4]); // Cambiar a 5 estrellas

  await waitFor(() => {
    expect(ratingsApi.ratingsApi.updateCourseRating).toHaveBeenCalledWith(1, 1, {
      user_id: 1,
      rating: 5,
    });
  });
});
```

#### Tests de Error Handling
```typescript
it('displays error message on failed submit', async () => {
  vi.mocked(ratingsApi.ratingsApi.addCourseRating).mockRejectedValue(
    new ratingsApi.ApiError('Network error', 500)
  );

  render(<RatingSection courseId={1} userId={1} />);

  const stars = screen.getAllByRole('button', { name: /Rate \d stars/ });
  await userEvent.click(stars[3]);

  await waitFor(() => {
    expect(screen.getByRole('alert')).toHaveTextContent(/Network error/);
  });
});

it('rolls back optimistic update on error', async () => {
  vi.mocked(ratingsApi.ratingsApi.addCourseRating).mockRejectedValue(
    new Error('Failed')
  );

  render(
    <RatingSection
      courseId={1}
      userId={1}
      initialAverageRating={4.0}
      initialTotalRatings={10}
    />
  );

  const stars = screen.getAllByRole('button', { name: /Rate \d stars/ });
  await userEvent.click(stars[4]); // Click 5 stars

  // Verificar que el promedio volvió al valor original
  await waitFor(() => {
    expect(screen.getByText(/Basado en 10 valoraciones/)).toBeInTheDocument();
  });
});
```

#### Tests de Loading States
```typescript
it('disables rating during submission', async () => {
  vi.mocked(ratingsApi.ratingsApi.addCourseRating).mockImplementation(
    () => new Promise(resolve => setTimeout(resolve, 100))
  );

  render(<RatingSection courseId={1} userId={1} />);

  const stars = screen.getAllByRole('button', { name: /Rate \d stars/ });
  await userEvent.click(stars[3]);

  // Durante el submit, los botones deben estar disabled
  stars.forEach(star => {
    expect(star).toBeDisabled();
  });

  expect(screen.getByText(/Guardando.../)).toBeInTheDocument();
});
```

### 6.3 Course Component Tests (Updated)

**Archivo**: `Frontend/src/components/Course/__test__/Course.test.tsx`

#### Tests adicionales para ratings
```typescript
it('renders rating when provided', () => {
  const courseWithRating = {
    ...mockCourse,
    averageRating: 4.5,
    totalRatings: 120,
  };

  render(<Course {...courseWithRating} />);

  expect(screen.getByText('(120)')).toBeInTheDocument();
});

it('does not render rating section when not provided', () => {
  render(<Course {...mockCourse} />);

  expect(screen.queryByText(/\(\d+\)/)).not.toBeInTheDocument();
});

it('handles zero rating correctly', () => {
  const courseWithZeroRating = {
    ...mockCourse,
    averageRating: 0,
    totalRatings: 0,
  };

  render(<Course {...courseWithZeroRating} />);

  // Debe renderizar rating (0 es válido)
  expect(screen.getByText('(0)')).toBeInTheDocument();
});
```

### 6.4 Accessibility Tests Completos

**Usando @testing-library/jest-dom y aXe**:

```typescript
import { axe, toHaveNoViolations } from 'jest-axe';
expect.extend(toHaveNoViolations);

it('StarRating has no accessibility violations', async () => {
  const { container } = render(<StarRating rating={3} />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});

it('RatingSection has no accessibility violations', async () => {
  const { container } = render(
    <RatingSection courseId={1} userId={1} />
  );
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

**Consideraciones**:
- Instalar `jest-axe` como devDependency
- Ejecutar en todos los componentes principales
- Validar contrastes, ARIA labels, semantic HTML

### 6.5 Visual Regression Tests (Opcional)

**Usando Vitest + Playwright Screenshot**:

```typescript
it('matches visual snapshot in default state', async () => {
  const { container } = render(<StarRating rating={3.5} />);
  expect(container).toMatchSnapshot();
});

it('matches visual snapshot in hover state', async () => {
  const { container } = render(<StarRating rating={2} />);
  const stars = screen.getAllByRole('button');
  await userEvent.hover(stars[3]);
  expect(container).toMatchSnapshot();
});
```

**Consideraciones**:
- Snapshots pueden ser frágiles (cambios de estilo rompen tests)
- Útil para detectar regresiones visuales
- Ejecutar en CI con viewport consistente

---

## Consideraciones Técnicas Finales

### Bundle Size Impact

**Estimación del impacto**:
- **StarRating Component**: ~2KB (gzipped)
- **RatingSection Component**: ~3KB (gzipped)
- **ratingsApi Service**: ~2KB (gzipped)
- **Types & Interfaces**: ~0.5KB (tree-shaken)
- **Total estimado**: ~7.5KB (gzipped)

**Optimizaciones**:
- SVG inline (evitar icon library pesada)
- No usar librerías externas (fetch nativo)
- Tree-shaking automático de Next.js
- Lazy load de RatingSection si es necesario

### Performance Considerations

**Métricas objetivo**:
- **First Contentful Paint (FCP)**: < 1.5s (no impactar)
- **Largest Contentful Paint (LCP)**: < 2.5s (no impactar)
- **Time to Interactive (TTI)**: < 3.5s (rating section no bloquea)
- **Cumulative Layout Shift (CLS)**: 0 (rating section no causa shift)

**Estrategias**:
- StarRating es componente ligero (no memo a menos que necesario)
- RatingSection usa useState (no context global innecesario)
- Optimistic updates evitan bloqueo de UI
- Server Components para data inicial (SSR)

### Security Considerations

**Validaciones**:
- Rating 1-5 validado en frontend y backend
- `user_id` validado (temporal hasta auth real)
- CORS configurado en backend para requests del frontend
- No exponer API keys en código cliente

**Future-proofing**:
- Preparar para autenticación JWT
- Campo `user_id` será reemplazado por token de sesión
- CSRF protection cuando se implemente auth

### Browser Compatibility

**Targets**:
- Chrome/Edge: Últimas 2 versiones
- Firefox: Últimas 2 versiones
- Safari: Últimas 2 versiones
- Mobile: iOS Safari 14+, Chrome Android 90+

**Polyfills necesarios** (Next.js los incluye):
- `fetch` (built-in en Next.js)
- `Promise`
- `Array.find`

**CSS compatibilidad**:
- CSS Variables (soportadas desde Chrome 49, Safari 9.1)
- Flexbox (soporte universal)
- CSS Modules (compilado por Next.js)

### Error Monitoring (Recomendado)

**Integración futura con Sentry o similar**:
```typescript
try {
  await ratingsApi.addCourseRating(courseId, data);
} catch (err) {
  // Log a servicio de monitoreo
  if (typeof window !== 'undefined' && window.Sentry) {
    window.Sentry.captureException(err);
  }

  handleError(err);
}
```

---

## Checklist de Implementación

### FASE 1: Types & Interfaces
- [ ] Crear interfaces `CourseRating`, `RatingRequest`, `RatingStats`
- [ ] Actualizar interface `Course` con campos opcionales
- [ ] Crear tipos de estado: `RatingState`, `RatingError`
- [ ] Implementar type guards: `isValidRating`, `isCourseRating`
- [ ] Verificar TypeScript strict compliance (no `any`)

### FASE 2: API Service Layer
- [ ] Crear archivo `ratingsApi.ts` en `src/services/`
- [ ] Configurar environment variable `NEXT_PUBLIC_API_URL`
- [ ] Implementar `fetchWithTimeout` helper
- [ ] Implementar `handleApiResponse` helper
- [ ] Crear clase `ApiError` customizada
- [ ] Implementar `getCourseRatings`
- [ ] Implementar `addCourseRating`
- [ ] Implementar `updateCourseRating`
- [ ] Implementar `deleteCourseRating`
- [ ] Implementar `getCourseWithRatings`
- [ ] Crear tests unitarios del service
- [ ] Validar manejo de errores HTTP

### FASE 3: StarRating Component
- [ ] Crear estructura de carpeta `StarRating/`
- [ ] Implementar `StarRating.tsx` con props interface
- [ ] Crear estados internos (hover, submitting)
- [ ] Implementar event handlers (click, hover, keyboard)
- [ ] Crear `StarIcon` sub-component con SVG
- [ ] Implementar lógica de half-stars
- [ ] Crear `StarRating.module.scss` con size variants
- [ ] Implementar ARIA labels y roles
- [ ] Añadir keyboard navigation (Arrow keys, Enter, Escape)
- [ ] Crear tests de renderizado
- [ ] Crear tests de interactividad
- [ ] Crear tests de accesibilidad
- [ ] Validar focus styles visibles

### FASE 4: Integration en Components
- [ ] Actualizar props de `Course` component
- [ ] Añadir `StarRating` readonly en Course card
- [ ] Actualizar `Course.module.scss` para rating section
- [ ] Crear `RatingSection.tsx` como Client Component
- [ ] Implementar estados de `RatingSection`
- [ ] Crear `useEffect` para cargar user rating
- [ ] Implementar `handleRatingChange` con optimistic updates
- [ ] Crear helper `calculateOptimisticAverage`
- [ ] Implementar rollback strategy en errores
- [ ] Crear `RatingSection.module.scss`
- [ ] Integrar `RatingSection` en `CourseDetail`
- [ ] Actualizar `page.tsx` para incluir rating data
- [ ] Validar fallbacks si backend no envía rating fields

### FASE 5: State Management & UX
- [ ] Implementar feedback visual (loading, error, success)
- [ ] Añadir animaciones de submit exitoso
- [ ] Implementar timeout automático de mensajes
- [ ] (Opcional) Añadir localStorage caché
- [ ] (Opcional) Implementar retry automático
- [ ] (Opcional) Detectar offline y auto-retry
- [ ] Validar estados disabled durante API calls
- [ ] Verificar que no haya memory leaks (cleanup effects)

### FASE 6: Testing
- [ ] Completar tests de `StarRating`
- [ ] Completar tests de `RatingSection`
- [ ] Actualizar tests de `Course` component
- [ ] Ejecutar tests de accesibilidad con axe
- [ ] Validar cobertura de tests >= 85%
- [ ] (Opcional) Crear visual regression tests
- [ ] Ejecutar `yarn test` y verificar todos pasan
- [ ] Verificar TypeScript compilation sin errores

### Validación Final
- [ ] Ejecutar `yarn dev` y probar flujo completo
- [ ] Verificar en Chrome, Firefox, Safari
- [ ] Validar responsive en mobile (360px, 768px, 1024px)
- [ ] Probar navegación por teclado completa
- [ ] Validar con screen reader (VoiceOver, NVDA)
- [ ] Verificar bundle size incrementado < 10KB
- [ ] Ejecutar `yarn build` exitosamente
- [ ] Validar en producción (staging environment)

---

## Estimación Final por Fase

| Fase | Descripción | Tiempo |
|------|-------------|--------|
| 1 | TypeScript Types & Interfaces | 30min |
| 2 | API Service Layer | 1.5h |
| 3 | StarRating Component | 2.5h |
| 4 | Integration en Components | 2h |
| 5 | State Management & UX | 1h |
| 6 | Testing Frontend | 1.5h |
| **TOTAL** | **Frontend Ratings Implementation** | **9h** |

**Nota**: Estimación incluye buffer para debugging y ajustes. Tiempo real puede variar según experiencia del desarrollador.

---

## Próximos Pasos Post-Implementación

1. **Documentación**:
   - Actualizar README con nuevas funcionalidades
   - Documentar props de `StarRating` en Storybook (opcional)
   - Crear guía de uso para futuros desarrolladores

2. **Integración con Auth**:
   - Reemplazar `userId` hardcoded con JWT token
   - Actualizar API calls para incluir Authorization header
   - Manejar casos de usuario no autenticado

3. **Analytics**:
   - Trackear eventos de rating (Google Analytics, Mixpanel)
   - Medir tasa de conversión de ratings
   - A/B testing de UI variants

4. **Mejoras Futuras**:
   - Implementar reviews de texto (además de rating)
   - Agregar filtros de ratings (ordenar por mejor valorados)
   - Implementar sistema de "helpful" votes en reviews
   - Añadir gráficos de distribución de ratings (histograma)

---

**Documento completo y listo para implementación.**
**Fecha de creación**: 2025-10-14
**Preparado para**: Frontend Team - Platziflix
