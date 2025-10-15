/**
 * Ratings API Service
 * Maneja todas las peticiones HTTP relacionadas con el sistema de ratings
 */

import type { CourseRating, RatingRequest, RatingStats } from '@/types/rating';
import { ApiError } from '@/types/rating';

// Base URL del backend API
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Opciones extendidas de fetch con timeout
interface FetchOptions extends RequestInit {
  timeout?: number;
}

/**
 * Helper: Fetch con timeout para prevenir requests colgados
 */
async function fetchWithTimeout(
  url: string,
  options: FetchOptions = {}
): Promise<Response> {
  const { timeout = 10000, ...fetchOptions } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        throw new ApiError('Request timeout', 408, 'TIMEOUT');
      }
      throw new ApiError(
        `Network error: ${error.message}`,
        0,
        'NETWORK_ERROR'
      );
    }

    throw new ApiError('Unknown error occurred', 0, 'UNKNOWN');
  }
}

/**
 * Helper: Procesa la respuesta de la API y maneja errores
 */
async function handleApiResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get('content-type');

  // Verificar que sea JSON
  if (!contentType || !contentType.includes('application/json')) {
    throw new ApiError(
      'Invalid response format',
      response.status,
      'INVALID_FORMAT'
    );
  }

  // Parsear el body
  const data = await response.json();

  // Si la respuesta no es OK, lanzar error con detalles
  if (!response.ok) {
    const message = data.detail || data.message || `HTTP ${response.status}`;
    throw new ApiError(message, response.status, data.code, data);
  }

  return data as T;
}

/**
 * GET /courses/{course_id}/ratings/stats
 * Obtiene las estadísticas de ratings de un curso
 */
async function getRatingStats(courseId: number): Promise<RatingStats> {
  const url = `${API_BASE_URL}/courses/${courseId}/ratings/stats`;

  try {
    const response = await fetchWithTimeout(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return await handleApiResponse<RatingStats>(response);
  } catch (error) {
    // Si el curso no tiene ratings (404), retornar stats vacías
    if (error instanceof ApiError && error.status === 404) {
      return {
        average_rating: 0,
        total_ratings: 0,
      };
    }
    throw error;
  }
}

/**
 * GET /courses/{course_id}/ratings
 * Obtiene todos los ratings de un curso
 */
async function getCourseRatings(courseId: number): Promise<CourseRating[]> {
  const url = `${API_BASE_URL}/courses/${courseId}/ratings`;

  try {
    const response = await fetchWithTimeout(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return await handleApiResponse<CourseRating[]>(response);
  } catch (error) {
    // Si no hay ratings (404), retornar array vacío
    if (error instanceof ApiError && error.status === 404) {
      return [];
    }
    throw error;
  }
}

/**
 * GET /courses/{course_id}/ratings/{user_id}
 * Obtiene el rating de un usuario específico para un curso
 */
async function getUserRating(
  courseId: number,
  userId: number
): Promise<CourseRating | null> {
  const url = `${API_BASE_URL}/courses/${courseId}/ratings/${userId}`;

  try {
    const response = await fetchWithTimeout(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return await handleApiResponse<CourseRating>(response);
  } catch (error) {
    // Si el usuario no ha calificado (404), retornar null
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

/**
 * POST /courses/{course_id}/ratings
 * Crea un nuevo rating para un curso
 */
async function createRating(
  courseId: number,
  request: RatingRequest
): Promise<CourseRating> {
  const url = `${API_BASE_URL}/courses/${courseId}/ratings`;

  const response = await fetchWithTimeout(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  return await handleApiResponse<CourseRating>(response);
}

/**
 * PUT /courses/{course_id}/ratings/{user_id}
 * Actualiza el rating existente de un usuario
 */
async function updateRating(
  courseId: number,
  userId: number,
  request: RatingRequest
): Promise<CourseRating> {
  const url = `${API_BASE_URL}/courses/${courseId}/ratings/${userId}`;

  const response = await fetchWithTimeout(url, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  return await handleApiResponse<CourseRating>(response);
}

/**
 * DELETE /courses/{course_id}/ratings/{user_id}
 * Elimina el rating de un usuario
 */
async function deleteRating(courseId: number, userId: number): Promise<void> {
  const url = `${API_BASE_URL}/courses/${courseId}/ratings/${userId}`;

  const response = await fetchWithTimeout(url, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // 204 No Content es exitoso
  if (response.status !== 204 && !response.ok) {
    await handleApiResponse<void>(response);
  }
}

// Export del servicio como objeto constante
export const ratingsApi = {
  getRatingStats,
  getCourseRatings,
  getUserRating,
  createRating,
  updateRating,
  deleteRating,
} as const;

// Export de ApiError para manejo en componentes
export { ApiError };
