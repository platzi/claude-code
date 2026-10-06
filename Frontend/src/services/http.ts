/**
 * Helpers HTTP compartidos por los servicios de API (timeout + errores tipados)
 */

import { ApiError } from '@/types/rating';

// Opciones extendidas de fetch con timeout
export interface FetchOptions extends RequestInit {
  timeout?: number;
}

/**
 * Fetch con timeout para prevenir requests colgados
 */
export async function fetchWithTimeout(
  url: string,
  options: FetchOptions = {}
): Promise<Response> {
  const { timeout = 10000, ...fetchOptions } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    return await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
    });
  } catch (error) {
    // DOMException no siempre hereda de Error (p. ej. en jsdom): se compara por nombre
    if ((error as { name?: string } | null)?.name === 'AbortError') {
      throw new ApiError('Request timeout', 408, 'TIMEOUT');
    }
    // fetch rechaza con TypeError ante fallos de red
    if (error instanceof TypeError) {
      throw new ApiError(`Network error: ${error.message}`, 0, 'NETWORK_ERROR');
    }
    // Cualquier otro error se propaga intacto: Next.js lanza errores internos
    // desde fetch (p. ej. para marcar una ruta como dinámica) que no deben envolverse.
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Procesa la respuesta de la API. Un 204 devuelve undefined; un error
 * lanza ApiError con el `code` del backend ({"detail", "code"}).
 */
export async function handleApiResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get('content-type');

  if (!contentType || !contentType.includes('application/json')) {
    throw new ApiError(
      response.ok ? 'Invalid response format' : `HTTP ${response.status}`,
      response.status,
      'INVALID_FORMAT'
    );
  }

  const data = await response.json();

  if (!response.ok) {
    const message = typeof data.detail === 'string' ? data.detail : `HTTP ${response.status}`;
    throw new ApiError(message, response.status, data.code, data);
  }

  return data as T;
}
