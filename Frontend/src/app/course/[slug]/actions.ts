"use server";

import { revalidatePath } from "next/cache";
import { getCurrentUserId } from "@/lib/currentUser";
import { ratingsApi, ApiError } from "@/services/ratingsApi";
import { isValidRating, type ActionResult } from "@/types/rating";

// Una Server Action es un endpoint público: los argumentos pueden venir de
// cualquier cliente, así que se validan aquí aunque la UI ya los restrinja.
function isValidCourseId(courseId: unknown): courseId is number {
  return typeof courseId === "number" && Number.isInteger(courseId) && courseId > 0;
}

function isValidSlug(slug: unknown): slug is string {
  return typeof slug === "string" && /^[^/?#\s]{1,255}$/.test(slug);
}

const NOT_AUTHENTICATED = "Debes iniciar sesión para calificar este curso.";

function toErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.code) {
      case "COURSE_NOT_FOUND":
        return "Este curso ya no está disponible.";
      case "UNAUTHENTICATED":
        return NOT_AUTHENTICATED;
      case "TIMEOUT":
      case "NETWORK_ERROR":
        return "No pudimos conectar con el servidor. Intenta de nuevo.";
    }
  }
  return "No pudimos guardar tu calificación. Intenta de nuevo.";
}

function revalidateCourse(slug: string) {
  revalidatePath(`/course/${slug}`);
  revalidatePath("/");
}

export async function rateCourse(
  courseId: number,
  slug: string,
  rating: number
): Promise<ActionResult> {
  if (!isValidCourseId(courseId) || !isValidSlug(slug) || !isValidRating(rating)) {
    return { ok: false, error: "Calificación inválida." };
  }

  const userId = await getCurrentUserId();
  if (userId === null) {
    return { ok: false, error: NOT_AUTHENTICATED };
  }

  try {
    const saved = await ratingsApi.upsertMyRating(courseId, userId, rating);
    revalidateCourse(slug);
    return { ok: true, rating: saved.rating };
  } catch (error) {
    return { ok: false, error: toErrorMessage(error) };
  }
}

export async function removeRating(courseId: number, slug: string): Promise<ActionResult> {
  if (!isValidCourseId(courseId) || !isValidSlug(slug)) {
    return { ok: false, error: "Solicitud inválida." };
  }

  const userId = await getCurrentUserId();
  if (userId === null) {
    return { ok: false, error: NOT_AUTHENTICATED };
  }

  try {
    await ratingsApi.deleteMyRating(courseId, userId);
  } catch (error) {
    // Si ya no había rating, el estado final es el pedido: se trata como éxito.
    if (!(error instanceof ApiError && error.code === "RATING_NOT_FOUND")) {
      return { ok: false, error: toErrorMessage(error) };
    }
  }

  revalidateCourse(slug);
  return { ok: true, rating: null };
}
