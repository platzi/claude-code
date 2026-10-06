import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("next/cache", () => ({ revalidatePath: vi.fn() }));
vi.mock("@/lib/currentUser", () => ({ getCurrentUserId: vi.fn() }));
vi.mock("@/services/ratingsApi", async (importOriginal) => {
  const original = await importOriginal<typeof import("@/services/ratingsApi")>();
  return {
    ...original,
    ratingsApi: { upsertMyRating: vi.fn(), deleteMyRating: vi.fn() },
  };
});

import { revalidatePath } from "next/cache";
import { getCurrentUserId } from "@/lib/currentUser";
import { ratingsApi, ApiError } from "@/services/ratingsApi";
import { rateCourse, removeRating } from "./actions";

const upsertMyRating = vi.mocked(ratingsApi.upsertMyRating);
const deleteMyRating = vi.mocked(ratingsApi.deleteMyRating);
const currentUser = vi.mocked(getCurrentUserId);

const SAVED = {
  id: 1,
  course_id: 3,
  user_id: 7,
  rating: 4,
  created_at: "2026-09-28T10:00:00",
  updated_at: "2026-09-28T10:00:00",
};

beforeEach(() => {
  vi.clearAllMocks();
  currentUser.mockResolvedValue(7);
});

describe("rateCourse", () => {
  it("saves the rating for the server-side user and revalidates detail and catalog", async () => {
    upsertMyRating.mockResolvedValue(SAVED);

    const result = await rateCourse(3, "curso-de-react", 4);

    expect(result).toEqual({ ok: true, rating: 4 });
    expect(upsertMyRating).toHaveBeenCalledWith(3, 7, 4);
    expect(revalidatePath).toHaveBeenCalledWith("/course/curso-de-react");
    expect(revalidatePath).toHaveBeenCalledWith("/");
  });

  it.each([7, 0, 3.5, Number.NaN, "5" as unknown as number])(
    "rejects rating %s without calling the API",
    async (rating) => {
      const result = await rateCourse(3, "curso-de-react", rating);

      expect(result).toEqual({ ok: false, error: "Calificación inválida." });
      expect(upsertMyRating).not.toHaveBeenCalled();
      expect(revalidatePath).not.toHaveBeenCalled();
    }
  );

  it.each([
    [0, "curso-de-react"],
    [-1, "curso-de-react"],
    [3, "../admin"],
    [3, ""],
  ])("rejects courseId %s / slug %j", async (courseId, slug) => {
    const result = await rateCourse(courseId, slug, 4);

    expect(result.ok).toBe(false);
    expect(upsertMyRating).not.toHaveBeenCalled();
  });

  it("fails without a current user", async () => {
    currentUser.mockResolvedValue(null);

    const result = await rateCourse(3, "curso-de-react", 4);

    expect(result).toEqual({
      ok: false,
      error: "Debes iniciar sesión para calificar este curso.",
    });
    expect(upsertMyRating).not.toHaveBeenCalled();
  });

  it("maps API errors to a message and does not revalidate", async () => {
    upsertMyRating.mockRejectedValue(new ApiError("Request timeout", 408, "TIMEOUT"));

    const result = await rateCourse(3, "curso-de-react", 4);

    expect(result).toEqual({
      ok: false,
      error: "No pudimos conectar con el servidor. Intenta de nuevo.",
    });
    expect(revalidatePath).not.toHaveBeenCalled();
  });
});

describe("removeRating", () => {
  it("deletes the rating and revalidates", async () => {
    deleteMyRating.mockResolvedValue(undefined);

    const result = await removeRating(3, "curso-de-react");

    expect(result).toEqual({ ok: true, rating: null });
    expect(deleteMyRating).toHaveBeenCalledWith(3, 7);
    expect(revalidatePath).toHaveBeenCalledWith("/course/curso-de-react");
  });

  it("treats RATING_NOT_FOUND as already removed", async () => {
    deleteMyRating.mockRejectedValue(
      new ApiError("User has not rated this course", 404, "RATING_NOT_FOUND")
    );

    const result = await removeRating(3, "curso-de-react");

    expect(result).toEqual({ ok: true, rating: null });
  });

  it("returns an error for other API failures", async () => {
    deleteMyRating.mockRejectedValue(new ApiError("boom", 500));

    const result = await removeRating(3, "curso-de-react");

    expect(result.ok).toBe(false);
    expect(revalidatePath).not.toHaveBeenCalled();
  });
});
