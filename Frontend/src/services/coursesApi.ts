/**
 * Courses API Service
 * Catálogo, detalle de curso y detalle de clase (solo lectura).
 */

import type { ClassDetail, Course, CourseDetail } from '@/types';
import { ApiError } from '@/types/rating';
import { API_URL } from '@/lib/config';
import { fetchWithTimeout, handleApiResponse } from './http';

const GET_OPTIONS: RequestInit = {
  method: 'GET',
  headers: { 'Content-Type': 'application/json' },
  cache: 'no-store', // datos frescos en cada request (ratings cambian seguido)
};

/** null si el recurso no existe (404); cualquier otro error se propaga */
async function getOrNull<T>(url: string): Promise<T | null> {
  const response = await fetchWithTimeout(url, GET_OPTIONS);

  try {
    return await handleApiResponse<T>(response);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

/**
 * GET /courses
 */
async function getCourses(): Promise<Course[]> {
  const response = await fetchWithTimeout(`${API_URL}/courses`, GET_OPTIONS);
  return handleApiResponse<Course[]>(response);
}

/**
 * GET /courses/{slug} — null si el curso no existe
 */
async function getCourseBySlug(slug: string): Promise<CourseDetail | null> {
  return getOrNull<CourseDetail>(`${API_URL}/courses/${encodeURIComponent(slug)}`);
}

/**
 * GET /classes/{class_id} — null si la clase no existe
 */
async function getClassById(classId: string | number): Promise<ClassDetail | null> {
  return getOrNull<ClassDetail>(`${API_URL}/classes/${encodeURIComponent(String(classId))}`);
}

export const coursesApi = {
  getCourses,
  getCourseBySlug,
  getClassById,
} as const;
