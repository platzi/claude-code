/**
 * Fuente única de la URL del backend.
 * API_URL se usa en el servidor (Server Components / Server Actions);
 * NEXT_PUBLIC_API_URL queda como fallback para código que corre en el navegador.
 */
export const API_URL =
  process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
