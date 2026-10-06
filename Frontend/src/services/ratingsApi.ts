/**
 * Ratings API Service
 * Maneja todas las peticiones HTTP relacionadas con el sistema de ratings.
 *
 * Las operaciones del usuario actual usan /ratings/me con el header X-User-Id
 * y deben llamarse solo desde el servidor (Server Components / Server Actions).
 */

import type { CourseRating, MyRatingRequest, RatingStats } from '@/types/rating';
import { ApiError } from '@/types/rating';
import { API_URL } from '@/lib/config';
import { fetchWithTimeout, handleApiResponse } from './http';

const JSON_HEADERS = { 'Content-Type': 'application/json' };

function ratingsUrl(courseId: number, path = ''): string {
  return `${API_URL}/courses/${courseId}/ratings${path}`;
}

function userHeaders(userId: number): HeadersInit {
  return { ...JSON_HEADERS, 'X-User-Id': String(userId) };
}

/**
 * GET /courses/{course_id}/ratings/stats
 * Un curso sin ratings responde stats en cero; un 404 (curso inexistente)
 * se propaga como ApiError con code COURSE_NOT_FOUND.
 */
async function getRatingStats(courseId: number): Promise<RatingStats> {
  const response = await fetchWithTimeout(ratingsUrl(courseId, '/stats'), {
    method: 'GET',
    headers: JSON_HEADERS,
  });

  return handleApiResponse<RatingStats>(response);
}

/**
 * GET /courses/{course_id}/ratings
 * Ratings activos de un curso (lista vacía si no hay)
 */
async function getCourseRatings(courseId: number): Promise<CourseRating[]> {
  const response = await fetchWithTimeout(ratingsUrl(courseId), {
    method: 'GET',
    headers: JSON_HEADERS,
  });

  return handleApiResponse<CourseRating[]>(response);
}

/**
 * GET /courses/{course_id}/ratings/me
 * Devuelve null solo si el usuario no ha calificado (RATING_NOT_FOUND);
 * un curso inexistente (COURSE_NOT_FOUND) sigue siendo un error.
 */
async function getMyRating(courseId: number, userId: number): Promise<CourseRating | null> {
  const response = await fetchWithTimeout(ratingsUrl(courseId, '/me'), {
    method: 'GET',
    headers: userHeaders(userId),
    cache: 'no-store',
  });

  try {
    return await handleApiResponse<CourseRating>(response);
  } catch (error) {
    if (error instanceof ApiError && error.code === 'RATING_NOT_FOUND') {
      return null;
    }
    throw error;
  }
}

/**
 * PUT /courses/{course_id}/ratings/me
 * Crea (201) o actualiza (200) el rating del usuario
 */
async function upsertMyRating(
  courseId: number,
  userId: number,
  rating: number
): Promise<CourseRating> {
  const body: MyRatingRequest = { rating };

  const response = await fetchWithTimeout(ratingsUrl(courseId, '/me'), {
    method: 'PUT',
    headers: userHeaders(userId),
    body: JSON.stringify(body),
  });

  return handleApiResponse<CourseRating>(response);
}

/**
 * DELETE /courses/{course_id}/ratings/me
 * 204 sin body si se eliminó; 404 RATING_NOT_FOUND si no había rating
 */
async function deleteMyRating(courseId: number, userId: number): Promise<void> {
  const response = await fetchWithTimeout(ratingsUrl(courseId, '/me'), {
    method: 'DELETE',
    headers: userHeaders(userId),
  });

  await handleApiResponse<void>(response);
}

// Export del servicio como objeto constante
export const ratingsApi = {
  getRatingStats,
  getCourseRatings,
  getMyRating,
  upsertMyRating,
  deleteMyRating,
} as const;

// Export de ApiError para manejo en componentes
export { ApiError };
