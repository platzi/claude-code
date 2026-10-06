/**
 * Rating Types & Interfaces
 * Sistema de calificaciones para cursos de Platziflix
 */

// Calificación de un curso por un usuario
export interface CourseRating {
  id: number;
  course_id: number;
  user_id: number;
  rating: number; // 1-5
  created_at: string; // ISO 8601
  updated_at: string; // ISO 8601
}

// Body de PUT /courses/{course_id}/ratings/me (el usuario va en el header X-User-Id)
export interface MyRatingRequest {
  rating: number; // 1-5
}

// Conteo de votos por estrella. Las claves llegan como string en el JSON.
export type RatingDistribution = Record<'1' | '2' | '3' | '4' | '5', number>;

// Estadísticas agregadas de ratings de un curso
export interface RatingStats {
  average_rating: number; // 0.0 - 5.0
  total_ratings: number; // Cantidad total
  rating_distribution: RatingDistribution;
}

// Estados de UI para operaciones de rating
export type RatingState = 'idle' | 'loading' | 'success' | 'error';

// Estructura de error para ratings
export interface RatingError {
  message: string;
  code?: string;
  details?: Record<string, unknown>;
}

/**
 * Type guard: Valida que un rating esté en el rango correcto (1-5)
 */
export function isValidRating(rating: number): rating is number {
  return Number.isInteger(rating) && rating >= 1 && rating <= 5;
}

/**
 * Type guard: Valida que un objeto sea un CourseRating válido
 */
export function isCourseRating(obj: unknown): obj is CourseRating {
  if (!obj || typeof obj !== 'object') return false;

  const candidate = obj as Record<string, unknown>;

  return (
    typeof candidate.id === 'number' &&
    typeof candidate.course_id === 'number' &&
    typeof candidate.user_id === 'number' &&
    typeof candidate.rating === 'number' &&
    isValidRating(candidate.rating) &&
    typeof candidate.created_at === 'string' &&
    typeof candidate.updated_at === 'string'
  );
}

const RATING_KEYS = ['1', '2', '3', '4', '5'] as const;

/**
 * Type guard: Valida que un objeto sea una distribución 1-5 válida
 */
export function isRatingDistribution(obj: unknown): obj is RatingDistribution {
  if (!obj || typeof obj !== 'object') return false;

  const candidate = obj as Record<string, unknown>;

  return RATING_KEYS.every(
    (key) => typeof candidate[key] === 'number' && (candidate[key] as number) >= 0
  );
}

/**
 * Type guard: Valida que un objeto sea RatingStats válido.
 * La distribución se valida solo si está presente.
 */
export function isRatingStats(obj: unknown): obj is RatingStats {
  if (!obj || typeof obj !== 'object') return false;

  const candidate = obj as Record<string, unknown>;

  return (
    typeof candidate.average_rating === 'number' &&
    candidate.average_rating >= 0 &&
    candidate.average_rating <= 5 &&
    typeof candidate.total_ratings === 'number' &&
    candidate.total_ratings >= 0 &&
    (candidate.rating_distribution === undefined ||
      isRatingDistribution(candidate.rating_distribution))
  );
}

/**
 * Custom Error class para errores de API
 */
export class ApiError extends Error {
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

/**
 * Resultado de las Server Actions de rating. `rating` es el valor guardado
 * (null tras quitar la calificación).
 */
export type ActionResult =
  | { ok: true; rating: number | null }
  | { ok: false; error: string };
